import secrets
from decimal import Decimal

from django.conf import settings
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.history import staff_history_user
from apps.core.models import SingletonModel, TimeStampedModel
from apps.orders.state import DeliveryMethod, OrderStatus, PaymentMethod, PaymentStatus


def new_public_token() -> str:
    return secrets.token_urlsafe(24)


class Order(TimeStampedModel):
    # Номер присвоюється після вставки (KER-<pk>), тому до того NULL, а не порожній рядок.
    number = models.CharField(  # noqa: DJ001
        "номер", max_length=20, unique=True, null=True, editable=False
    )
    public_token = models.CharField(max_length=64, unique=True, default=new_public_token,
                                    editable=False)
    status = models.CharField("статус", max_length=20, choices=OrderStatus.choices,
                              default=OrderStatus.NEW, editable=False)
    payment_method = models.CharField("оплата", max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField("статус оплати", max_length=20,
                                      choices=PaymentStatus.choices, editable=False)
    needs_review = models.BooleanField("потребує перевірки", default=False)
    customer_name = models.CharField("ім'я", max_length=150)
    phone = models.CharField("телефон", max_length=32)
    email = models.EmailField("email", blank=True)
    comment = models.TextField("коментар", blank=True)
    delivery_method = models.CharField("доставка", max_length=20,
                                       choices=DeliveryMethod.choices)
    delivery = models.JSONField("адреса доставки", default=dict, blank=True)
    subtotal_kop = models.PositiveIntegerField("товари, коп.", default=0, editable=False)
    delivery_kop = models.PositiveIntegerField("доставка, коп.", null=True, blank=True)
    total_kop = models.PositiveIntegerField("разом, коп.", default=0, editable=False)
    weight_kg = models.DecimalField("вага, кг", max_digits=10, decimal_places=3,
                                    default=Decimal("0"), editable=False)
    estimate = models.ForeignKey("calc.Estimate", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="orders",
                                 verbose_name="кошторис")
    idempotency_key = models.CharField(max_length=64, unique=True, null=True, blank=True,
                                       editable=False)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="orders",
                                verbose_name="менеджер")
    customer = models.ForeignKey("customers.Customer", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="orders",
                                 verbose_name="клієнт")
    confirmed_at = models.DateTimeField(null=True, blank=True, editable=False)
    shipped_at = models.DateTimeField(null=True, blank=True, editable=False)
    completed_at = models.DateTimeField(null=True, blank=True, editable=False)
    cancelled_at = models.DateTimeField(null=True, blank=True, editable=False)
    paid_at = models.DateTimeField(null=True, blank=True, editable=False)
    reminded_at = models.DateTimeField(null=True, blank=True, editable=False)

    history = HistoricalRecords(get_user=staff_history_user)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "замовлення"
        verbose_name_plural = "замовлення"
        indexes = [models.Index(fields=["status", "created_at"]), models.Index(fields=["phone"])]

    def __str__(self) -> str:
        return self.number or f"Замовлення {self.pk}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="+")
    sku = models.CharField("артикул", max_length=64)
    name = models.CharField("назва", max_length=255)
    unit = models.CharField("одиниця", max_length=10)
    qty = models.PositiveIntegerField("кількість")
    qty_base = models.DecimalField("обсяг (м² або од.)", max_digits=12, decimal_places=3)
    price_kop = models.PositiveIntegerField("ціна, коп.")
    total_kop = models.PositiveIntegerField("сума, коп.")
    weight_kg = models.DecimalField("вага, кг", max_digits=10, decimal_places=3,
                                    default=Decimal("0"))
    reserved_qty = models.DecimalField("зарезервовано", max_digits=12, decimal_places=3,
                                       default=Decimal("0"), editable=False)
    group_label = models.CharField("група", max_length=100, blank=True)

    class Meta:
        ordering = ["id"]
        verbose_name = "позиція"
        verbose_name_plural = "позиції"

    def __str__(self) -> str:
        return f"{self.name} × {self.qty}"


class OrderEvent(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    from_status = models.CharField(max_length=20, choices=OrderStatus.choices, blank=True)
    to_status = models.CharField(max_length=20, choices=OrderStatus.choices)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                              on_delete=models.SET_NULL, related_name="+")
    comment = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        verbose_name = "подія замовлення"
        verbose_name_plural = "історія статусів"

    def __str__(self) -> str:
        return f"{self.from_status or '—'} → {self.to_status}"


class OrderSettings(SingletonModel):
    remind_after_minutes = models.PositiveIntegerField(
        "нагадувати про непідтверджене замовлення через, хв", default=60
    )

    class Meta:
        verbose_name = "налаштування замовлень"
        verbose_name_plural = "налаштування замовлень"

    def __str__(self) -> str:
        return "Налаштування замовлень"
