"""Статуси замовлення і дозволені переходи. Змінювати статус — лише через services.transition."""

from django.db import models


class OrderStatus(models.TextChoices):
    NEW = "new", "Нове"
    CONFIRMED = "confirmed", "Підтверджене"
    PACKED = "packed", "Зібране"
    SHIPPED = "shipped", "Відправлене"
    COMPLETED = "completed", "Виконане"
    CANCELLED = "cancelled", "Скасоване"


class PaymentStatus(models.TextChoices):
    AWAITING = "awaiting", "Очікує оплати"
    PAID = "paid", "Оплачено"
    REFUNDED = "refunded", "Повернено"
    ON_DELIVERY = "on_delivery", "Оплата при отриманні"


class PaymentMethod(models.TextChoices):
    ONLINE = "online", "Онлайн карткою"
    COD = "cod", "При отриманні"
    INVOICE = "invoice", "Рахунок для юросіб"


class DeliveryMethod(models.TextChoices):
    PICKUP = "pickup", "Самовивіз"
    LOCAL = "local", "Доставка по місту"
    NOVA_POSHTA = "nova_poshta", "Нова пошта"


TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.NEW: frozenset({OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.PACKED, OrderStatus.CANCELLED}),
    OrderStatus.PACKED: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.COMPLETED}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}

# Статуси, у яких залишок зарезервований.
RESERVED_STATUSES = frozenset({OrderStatus.CONFIRMED, OrderStatus.PACKED})


def can_transition(current: str, target: str) -> bool:
    return target in TRANSITIONS.get(current, frozenset())
