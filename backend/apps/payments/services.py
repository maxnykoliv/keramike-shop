"""Створення оплат, обробка webhook і повернення коштів."""

from typing import Any

import structlog
from django.conf import settings
from django.db import transaction

from apps.core.exceptions import DomainError, NotFound, ProviderUnavailable
from apps.orders import selectors as order_selectors
from apps.orders import services as order_services
from apps.orders.models import Order
from apps.orders.state import OrderStatus, PaymentMethod, PaymentStatus
from apps.payments.models import Payment
from apps.payments.providers import get_provider

logger = structlog.get_logger(__name__)


def start_payment(order: Order) -> Payment | None:
    """Створює посилання на оплату. Викликати після коміту замовлення."""
    if order.payment_method != PaymentMethod.ONLINE:
        return None
    if order.payment_status == PaymentStatus.PAID:
        raise DomainError("Замовлення вже оплачене", code="already_paid")
    if order.status == OrderStatus.CANCELLED:
        raise DomainError("Замовлення скасоване", code="order_cancelled")

    provider = get_provider()
    payment = Payment.objects.create(order=order, provider=provider.name,
                                     amount_kop=order.total_kop)
    try:
        link = provider.create_payment(
            reference=payment.reference,
            amount_kop=order.total_kop,
            description=f"Замовлення {order.number}",
            result_url=f"{settings.SITE_URL}/orders/{order.public_token}",
            server_url=f"{settings.API_URL}/api/v1/payments/webhook/{provider.name}",
        )
    except Exception as exc:
        payment.status = Payment.Status.FAILED
        payment.save(update_fields=["status", "updated_at"])
        logger.exception("payment_create_failed", order=order.number)
        raise ProviderUnavailable("Не вдалося створити оплату, спробуйте ще раз") from exc

    payment.status = Payment.Status.PENDING
    payment.payment_url = link.url
    payment.provider_payment_id = link.provider_payment_id
    payment.save(update_fields=["status", "payment_url", "provider_payment_id", "updated_at"])
    return payment


def handle_webhook(provider_name: str, data: dict[str, Any]) -> Payment:
    result = get_provider(provider_name).verify_webhook(data)
    with transaction.atomic():
        payment = Payment.objects.select_for_update().filter(reference=result.reference).first()
        if payment is None:
            raise NotFound("Оплату не знайдено")
        if payment.status == result.status:
            return payment  # повторний webhook

        payment.status = result.status
        payment.raw = result.raw
        if result.provider_payment_id:
            payment.provider_payment_id = result.provider_payment_id
        payment.save(update_fields=["status", "raw", "provider_payment_id", "updated_at"])

        if result.status == Payment.Status.SUCCEEDED:
            order_services.mark_paid(payment.order_id, result.amount_kop)
        elif result.status == Payment.Status.REFUNDED:
            order_services.mark_refunded(payment.order_id)
    return payment


def refund_cancelled_order(payload: dict[str, Any]) -> None:
    """Обробник події order.cancelled: повертає гроші, якщо замовлення було оплачене."""
    order = order_selectors.get_order(payload["order_id"])
    if order.payment_status != PaymentStatus.PAID:
        return
    payment = (Payment.objects.filter(order=order, status=Payment.Status.SUCCEEDED)
               .order_by("-created_at").first())
    if payment is None:
        return
    get_provider(payment.provider).refund(reference=payment.reference,
                                          amount_kop=payment.amount_kop)
    payment.status = Payment.Status.REFUND_REQUESTED
    payment.save(update_fields=["status", "updated_at"])
