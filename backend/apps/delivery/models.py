from django.db import models

from apps.core.models import SingletonModel, TimeStampedModel


class Shipment(TimeStampedModel):
    class Carrier(models.TextChoices):
        NOVA_POSHTA = "nova_poshta", "Нова пошта"
        LOCAL = "local", "Власна доставка"

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        CREATED = "created", "ТТН створено"
        IN_TRANSIT = "in_transit", "В дорозі"
        DELIVERED = "delivered", "Отримано"
        RETURNED = "returned", "Повернення"
        CANCELLED = "cancelled", "Скасовано"

    order = models.ForeignKey("orders.Order", on_delete=models.PROTECT,
                              related_name="shipments", verbose_name="замовлення")
    carrier = models.CharField("перевізник", max_length=20, choices=Carrier.choices)
    status = models.CharField("статус", max_length=20, choices=Status.choices,
                              default=Status.DRAFT)
    ttn = models.CharField("ТТН", max_length=40, blank=True, db_index=True)
    cost_kop = models.PositiveIntegerField("вартість, коп.", null=True, blank=True)
    raw = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "відправлення"
        verbose_name_plural = "відправлення"

    def __str__(self) -> str:
        return self.ttn or f"Відправлення {self.pk}"


class DeliverySettings(SingletonModel):
    local_delivery_kop = models.PositiveIntegerField(
        "доставка по місту, коп.", null=True, blank=True,
        help_text="Порожньо — вартість уточнює менеджер",
    )
    np_sender_ref = models.CharField("Нова пошта: відправник (Ref)", max_length=64, blank=True)
    np_sender_contact_ref = models.CharField("Нова пошта: контакт відправника (Ref)",
                                             max_length=64, blank=True)
    np_sender_city_ref = models.CharField("Нова пошта: місто відправника (Ref)",
                                          max_length=64, blank=True)
    np_sender_warehouse_ref = models.CharField("Нова пошта: відділення відправника (Ref)",
                                               max_length=64, blank=True)
    np_sender_phone = models.CharField("Нова пошта: телефон відправника", max_length=20,
                                       blank=True)

    class Meta:
        verbose_name = "налаштування доставки"
        verbose_name_plural = "налаштування доставки"

    def __str__(self) -> str:
        return "Налаштування доставки"
