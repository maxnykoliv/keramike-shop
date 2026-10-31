"""Вхід клієнтів: сесії, Telegram-бот, одноразові коди."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import structlog
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.core import events
from apps.core.exceptions import DomainError, NotFound
from apps.core.phone import InvalidPhone, normalize_phone
from apps.customers import telegram
from apps.customers.channels import get_channel
from apps.customers.events import CUSTOMER_LOGGED_IN
from apps.customers.models import (
    Customer,
    CustomerAddress,
    CustomerSession,
    PhoneCode,
    TelegramLogin,
)

logger = structlog.get_logger(__name__)

LOGIN_TTL = timedelta(minutes=10)
CODE_TTL = timedelta(minutes=10)
CODE_RESEND_AFTER = timedelta(seconds=60)
CODE_MAX_PER_HOUR = 5
CODE_MAX_ATTEMPTS = 5
SESSION_TOUCH_EVERY = timedelta(hours=12)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class LoginResult:
    customer: Customer
    token: str
    session: CustomerSession


# --- Сесії -----------------------------------------------------------------


def _session_ttl() -> timedelta:
    return timedelta(days=settings.CUSTOMER_SESSION_DAYS)


@transaction.atomic
def login(customer: Customer, *, user_agent: str = "", ip: str | None = None) -> LoginResult:
    if not customer.is_active:
        raise DomainError("Обліковий запис заблоковано", code="customer_blocked")
    token = secrets.token_urlsafe(32)
    now = timezone.now()
    session = CustomerSession.objects.create(
        customer=customer,
        key_hash=_hash(token),
        expires_at=now + _session_ttl(),
        last_used_at=now,
        user_agent=user_agent[:255],
        ip=ip,
    )
    customer.last_login_at = now
    customer.save(update_fields=["last_login_at", "updated_at"])
    events.publish(CUSTOMER_LOGGED_IN, {"customer_id": customer.pk, "phone": customer.phone})
    return LoginResult(customer=customer, token=token, session=session)


def authenticate_token(token: str) -> CustomerSession | None:
    session = (
        CustomerSession.objects.select_related("customer").filter(key_hash=_hash(token)).first()
    )
    now = timezone.now()
    if session is None or session.expires_at <= now or not session.customer.is_active:
        return None
    if now - session.last_used_at > SESSION_TOUCH_EVERY:
        # Ковзний термін: активні клієнти не розлогінюються.
        CustomerSession.objects.filter(pk=session.pk).update(
            last_used_at=now, expires_at=now + _session_ttl()
        )
    return session


def logout(session: CustomerSession) -> None:
    CustomerSession.objects.filter(pk=session.pk).delete()


def logout_all(customer: Customer) -> int:
    deleted, _ = CustomerSession.objects.filter(customer=customer).delete()
    return deleted


@transaction.atomic
def get_or_create_customer(
    phone: str, *, telegram_user_id: int | None = None, telegram_username: str = "", name: str = ""
) -> Customer:
    phone = normalize_phone(phone)
    customer = None
    if telegram_user_id:
        customer = (
            Customer.objects.select_for_update().filter(telegram_user_id=telegram_user_id).first()
        )
        # Номер у Telegram змінився: переносимо, якщо новий ще ні за ким не закріплений.
        if (customer and customer.phone != phone
                and not Customer.objects.filter(phone=phone).exclude(pk=customer.pk).exists()):
            customer.phone = phone
            customer.save(update_fields=["phone", "updated_at"])
    if customer is None:
        customer, _ = Customer.objects.select_for_update().get_or_create(
            phone=phone, defaults={"name": name}
        )
    changed = []
    if telegram_user_id and customer.telegram_user_id != telegram_user_id:
        Customer.objects.filter(telegram_user_id=telegram_user_id).exclude(pk=customer.pk).update(
            telegram_user_id=None
        )
        customer.telegram_user_id = telegram_user_id
        changed.append("telegram_user_id")
    if telegram_username and customer.telegram_username != telegram_username:
        customer.telegram_username = telegram_username
        changed.append("telegram_username")
    if name and not customer.name:
        customer.name = name
        changed.append("name")
    if changed:
        customer.save(update_fields=[*changed, "updated_at"])
    return customer


# --- Вхід через Telegram ----------------------------------------------------


def start_telegram_login() -> tuple[TelegramLogin, str]:
    """Повертає спробу входу і секрет опитування, який знає лише браузер."""
    if not settings.TELEGRAM_LOGIN_BOT_USERNAME:
        raise DomainError("Вхід через Telegram не налаштований", code="channel_unavailable")
    poll_secret = secrets.token_urlsafe(24)
    attempt = TelegramLogin.objects.create(
        start_token=secrets.token_urlsafe(24),
        poll_secret_hash=_hash(poll_secret),
        expires_at=timezone.now() + LOGIN_TTL,
    )
    return attempt, poll_secret


def _reply(chat_id: int, text: str, reply_markup: dict[str, Any] | None = None) -> None:
    """Відповідь бота — лише після коміту: HTTP-запитів усередині транзакції не робимо."""
    transaction.on_commit(lambda: telegram.send_message(chat_id, text, reply_markup=reply_markup))


def _full_name(user: dict[str, Any]) -> str:
    return " ".join(p for p in [user.get("first_name"), user.get("last_name")] if p).strip()


def _confirm(attempt: TelegramLogin, phone: str) -> None:
    attempt.phone = phone
    attempt.status = TelegramLogin.Status.CONFIRMED
    attempt.confirmed_at = timezone.now()
    attempt.save()
    _reply(
        attempt.telegram_chat_id or 0,
        "Готово, вхід підтверджено. Поверніться на сайт.",
        telegram.REMOVE_KEYBOARD,
    )


def _on_start(message: dict[str, Any], start_token: str) -> None:
    sender = message.get("from") or {}
    chat_id = message["chat"]["id"]
    with transaction.atomic():
        attempt = (
            TelegramLogin.objects.select_for_update()
            .filter(
                start_token=start_token,
                status=TelegramLogin.Status.PENDING,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if attempt is None:
            _reply(
                chat_id,
                "Посилання для входу застаріло. Натисніть «Увійти через Telegram» на сайті ще раз.",
            )
            return
        attempt.telegram_user_id = sender.get("id")
        attempt.telegram_chat_id = chat_id
        attempt.telegram_username = sender.get("username", "")
        attempt.telegram_name = _full_name(sender)
        known = Customer.objects.filter(telegram_user_id=sender.get("id"), is_active=True).first()
        if known:
            _confirm(attempt, known.phone)
            return
        attempt.status = TelegramLogin.Status.AWAITING_CONTACT
        attempt.save()
    _reply(
        chat_id, "Щоб увійти, поділіться номером телефону кнопкою нижче.", telegram.CONTACT_KEYBOARD
    )


def _on_contact(message: dict[str, Any]) -> None:
    sender = message.get("from") or {}
    contact = message["contact"]
    chat_id = message["chat"]["id"]
    if contact.get("user_id") != sender.get("id"):
        _reply(
            chat_id,
            "Надішліть, будь ласка, власний номер кнопкою нижче.",
            telegram.CONTACT_KEYBOARD,
        )
        return
    try:
        phone = normalize_phone(contact.get("phone_number", ""))
    except InvalidPhone:
        _reply(chat_id, "Не вдалося розпізнати номер телефону.")
        return
    with transaction.atomic():
        attempt = (
            TelegramLogin.objects.select_for_update()
            .filter(
                telegram_user_id=sender.get("id"),
                status=TelegramLogin.Status.AWAITING_CONTACT,
                expires_at__gt=timezone.now(),
            )
            .order_by("-created_at")
            .first()
        )
        if attempt is None:
            _reply(
                chat_id,
                "Спершу натисніть «Увійти через Telegram» на сайті.",
                telegram.REMOVE_KEYBOARD,
            )
            return
        _confirm(attempt, phone)


def handle_telegram_update(update: dict[str, Any]) -> None:
    message = update.get("message") or {}
    if not message.get("chat"):
        return
    text = (message.get("text") or "").strip()
    if message.get("contact"):
        _on_contact(message)
    elif text.startswith("/start"):
        parts = text.split(maxsplit=1)
        if len(parts) == 2:
            _on_start(message, parts[1])
        else:
            _reply(
                message["chat"]["id"],
                "Вітаємо! Щоб увійти, натисніть «Увійти через Telegram» на сайті Keramike.",
            )


def poll_telegram_login(
    login_id: str, poll_secret: str, *, user_agent: str = "", ip: str | None = None
) -> tuple[str, LoginResult | None]:
    with transaction.atomic():
        attempt = TelegramLogin.objects.select_for_update().filter(pk=login_id).first()
        if attempt is None or not hmac.compare_digest(attempt.poll_secret_hash, _hash(poll_secret)):
            raise NotFound("Спробу входу не знайдено")
        if attempt.status == TelegramLogin.Status.CONSUMED:
            raise NotFound("Спробу входу вже використано")
        if attempt.status != TelegramLogin.Status.CONFIRMED:
            if attempt.expires_at <= timezone.now():
                return "expired", None
            return attempt.status, None
        attempt.status = TelegramLogin.Status.CONSUMED
        attempt.save(update_fields=["status"])
        customer = get_or_create_customer(
            attempt.phone,
            telegram_user_id=attempt.telegram_user_id,
            telegram_username=attempt.telegram_username,
            name=attempt.telegram_name,
        )
        return "confirmed", login(customer, user_agent=user_agent, ip=ip)


# --- Одноразові коди (Viber, SMS) -------------------------------------------


def request_code(phone: str, channel_name: str) -> PhoneCode:
    channel = get_channel(channel_name)
    phone = normalize_phone(phone)
    now = timezone.now()
    recent = PhoneCode.objects.filter(phone=phone, created_at__gt=now - timedelta(hours=1))
    if recent.filter(created_at__gt=now - CODE_RESEND_AFTER).exists():
        raise DomainError("Код уже надіслано, повторно можна через хвилину", code="code_too_soon")
    if recent.count() >= CODE_MAX_PER_HOUR:
        raise DomainError("Забагато спроб, спробуйте пізніше", code="code_limit")
    code = f"{secrets.randbelow(1_000_000):06d}"
    record = PhoneCode.objects.create(
        phone=phone,
        channel=channel.name,
        code_hash=_hash(f"{phone}:{code}"),
        expires_at=now + CODE_TTL,
    )
    channel.send_code(phone, code)
    return record


def verify_code(
    phone: str, code: str, *, user_agent: str = "", ip: str | None = None
) -> LoginResult:
    phone = normalize_phone(phone)
    with transaction.atomic():
        record = (
            PhoneCode.objects.select_for_update()
            .filter(phone=phone, used_at__isnull=True, expires_at__gt=timezone.now())
            .order_by("-created_at")
            .first()
        )
        if record is None or record.attempts >= CODE_MAX_ATTEMPTS:
            raise DomainError("Код недійсний, запросіть новий", field="code", code="code_invalid")
        if not hmac.compare_digest(record.code_hash, _hash(f"{phone}:{code.strip()}")):
            record.attempts += 1
            record.save(update_fields=["attempts"])
            raise DomainError("Невірний код", field="code", code="code_invalid")
        record.used_at = timezone.now()
        record.save(update_fields=["used_at"])
    customer = get_or_create_customer(phone)
    return login(customer, user_agent=user_agent, ip=ip)


# --- Кабінет -----------------------------------------------------------------


@transaction.atomic
def set_default_address(address: CustomerAddress) -> None:
    address.customer.addresses.exclude(pk=address.pk).update(is_default=False)
    if not address.is_default:
        address.is_default = True
        address.save(update_fields=["is_default", "updated_at"])


@transaction.atomic
def set_master(customer: Customer, is_master: bool) -> Customer:
    customer.is_master = is_master
    customer.master_since = timezone.now() if is_master else None
    customer.save(update_fields=["is_master", "master_since", "updated_at"])
    return customer
