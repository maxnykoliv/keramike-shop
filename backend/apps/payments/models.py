import uuid

from django.db import models

from apps.core.models import TimeStampedModel


def new_reference() -> str:
    return uuid.uuid4().hex


class Payment(TimeStampedModel):
    class Status(models.TextChoices):
        CREATED = "created", "Створено"
        PENDING = "pending", "Очікує"
        SUCCEEDED = "succeeded", "Успішно"
        FAILED = "failed", "Помилка"
        REFUND_REQUESTED = "refund_requested", "Запит на повернення"
        REFUNDED = "refunded", "Повернено"

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT, related_name="payments",
                              verbose_name="замовлення")
    provider = models.CharField("провайдер", max_length=20)
    # Our identifier, sent to the provider as order_id.
    reference = models.CharField(max_length=40, unique=True, default=new_reference,
                                 editable=False)
    provider_payment_id = models.CharField(max_length=100, blank=True)
    amount_kop = models.PositiveIntegerField("сума, коп.")
    status = models.CharField("статус", max_length=20, choices=Status.choices,
                              default=Status.CREATED)
    payment_url = models.URLField(max_length=2000, blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "оплата"
        verbose_name_plural = "оплати"

    def __str__(self) -> str:
        return f"{self.reference} ({self.get_status_display()})"
