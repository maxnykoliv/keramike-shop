from datetime import timedelta

from django.db.models import QuerySet
from django.utils import timezone

from apps.core.exceptions import NotFound
from apps.orders.models import Order, OrderSettings
from apps.orders.state import OrderStatus


def get_order(order_id: int) -> Order:
    order = Order.objects.prefetch_related("items").filter(pk=order_id).first()
    if order is None:
        raise NotFound("Замовлення не знайдено")
    return order


def get_by_token(token: str) -> Order:
    order = Order.objects.prefetch_related("items", "events").filter(public_token=token).first()
    if order is None:
        raise NotFound("Замовлення не знайдено")
    return order


def customer_orders(customer_id: int) -> QuerySet[Order]:
    return Order.objects.filter(customer_id=customer_id).prefetch_related("items")


def find_by_idempotency_key(key: str) -> Order | None:
    return Order.objects.filter(idempotency_key=key).first()


def unconfirmed_for_reminder() -> QuerySet[Order]:
    minutes = OrderSettings.load().remind_after_minutes
    cutoff = timezone.now() - timedelta(minutes=minutes)
    return Order.objects.filter(status=OrderStatus.NEW, created_at__lt=cutoff,
                                reminded_at__isnull=True)
