import uuid

from django.db import models

from apps.core.models import TimeStampedModel


class Customer(TimeStampedModel):
    """Клієнт сайту. Не плутати з персоналом (accounts.User), який входить в адмінку."""

    phone = models.CharField("телефон", max_length=16, unique=True)
    name = models.CharField("ім'я", max_length=150, blank=True)
    email = models.EmailField("email", blank=True)
    is_master = models.BooleanField("майстер", default=False,
                                    help_text="Бачить і купує за цінами для майстрів")
    master_since = models.DateTimeField("майстер з", null=True, blank=True, editable=False)
    telegram_user_id = models.BigIntegerField("Telegram ID", unique=True, null=True,
                                              blank=True, editable=False)
    telegram_username = models.CharField("Telegram", max_length=64, blank=True,
                                         editable=False)
    is_active = models.BooleanField("активний", default=True)
    last_login_at = models.DateTimeField("останній вхід", null=True, blank=True,
                                         editable=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "клієнт"
        verbose_name_plural = "клієнти"

    def __str__(self) -> str:
        return f"{self.name or 'Без імені'}, {self.phone}"

    # Потрібно DRF: request.user — це клієнт.
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False


class CustomerAddress(TimeStampedModel):
    class Method(models.TextChoices):
        LOCAL = "local", "Доставка по місту"
        NOVA_POSHTA = "nova_poshta", "Нова пошта"

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField("назва", max_length=60, blank=True)
    delivery_method = models.CharField("спосіб", max_length=20, choices=Method.choices)
    city_ref = models.CharField(max_length=64, blank=True)
    city_name = models.CharField("місто", max_length=200, blank=True)
    warehouse_ref = models.CharField(max_length=64, blank=True)
    warehouse_name = models.CharField("відділення", max_length=255, blank=True)
    address = models.CharField("адреса", max_length=500, blank=True)
    is_default = models.BooleanField("основна", default=False)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name = "адреса"
        verbose_name_plural = "адреси"

    def __str__(self) -> str:
        return self.label or self.warehouse_name or self.address


class CustomerSession(models.Model):
    """Сесія клієнта. Зберігаємо лише SHA-256 токена, сам токен знає тільки браузер."""

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="sessions")
    key_hash = models.CharField(max_length=64, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used_at = models.DateTimeField()
    user_agent = models.CharField(max_length=255, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-last_used_at"]
        verbose_name = "сесія"
        verbose_name_plural = "сесії"

    def __str__(self) -> str:
        return f"{self.customer.phone}, {self.user_agent[:40]}"


class TelegramLogin(models.Model):
    """Спроба входу через Telegram-бота: сайт створює її, бот підтверджує номер."""

    class Status(models.TextChoices):
        PENDING = "pending", "Очікує бота"
        AWAITING_CONTACT = "awaiting_contact", "Очікує номер"
        CONFIRMED = "confirmed", "Підтверджено"
        CONSUMED = "consumed", "Використано"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    start_token = models.CharField(max_length=64, unique=True)
    poll_secret_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    telegram_user_id = models.BigIntegerField(null=True, blank=True, db_index=True)
    telegram_chat_id = models.BigIntegerField(null=True, blank=True)
    telegram_username = models.CharField(max_length=64, blank=True)
    telegram_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=16, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "вхід через Telegram"
        verbose_name_plural = "входи через Telegram"

    def __str__(self) -> str:
        return f"{self.get_status_display()} {self.phone}"


class PhoneCode(models.Model):
    """Одноразовий код для входу через Viber або SMS. Зберігаємо лише хеш коду."""

    phone = models.CharField(max_length=16, db_index=True)
    channel = models.CharField(max_length=20)
    code_hash = models.CharField(max_length=64)
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.phone} ({self.channel})"
