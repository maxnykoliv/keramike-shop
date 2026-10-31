from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Lead(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", "Нова"
        IN_PROGRESS = "in_progress", "В роботі"
        CONVERTED = "converted", "Замовлення створено"
        REJECTED = "rejected", "Відмова"

    estimate = models.ForeignKey("calc.Estimate", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="leads",
                                 verbose_name="кошторис")
    name = models.CharField("ім'я", max_length=150)
    phone = models.CharField("телефон", max_length=32)
    comment = models.TextField("коментар", blank=True)
    status = models.CharField("статус", max_length=20, choices=Status.choices,
                              default=Status.NEW)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL,
                              related_name="+", verbose_name="замовлення", editable=False)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="leads",
                                verbose_name="менеджер")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "заявка"
        verbose_name_plural = "заявки"

    def __str__(self) -> str:
        return f"{self.name}, {self.phone}"
