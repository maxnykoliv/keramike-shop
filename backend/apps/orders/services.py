"""The single place where order state changes."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.catalog import services as catalog_services
from apps.catalog.selectors import LinePrice, line_price, products_by_ids
from apps.core import events as bus
from apps.core.exceptions import (
    DomainError,
    InvalidTransition,
    NotFound,
    OutOfStock,
    PaymentRequired,
)
from apps.orders import events
from apps.orders.models import Order, OrderEvent, OrderItem
from apps.orders.state import (
    RESERVED_STATUSES,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
    can_transition,
)


@dataclass(frozen=True)
class Customer:
    name: str
    phone: str
    email: str = ""
    comment: str = ""


@dataclass(frozen=True)
class LineRequest:
    product_id: int
    qty: int
    group_label: str = ""


@dataclass(frozen=True)
class PricedLine:
    price: LinePrice
    group_label: str


def build_lines(requests: list[LineRequest], *, require_available: bool = True,
                master: bool = False) -> list[PricedLine]:
    """Prices lines at current DB prices. Prices from the browser are never trusted."""
    products = products_by_ids([r.product_id for r in requests])
    lines = []
    for request in requests:
        product = products.get(request.product_id)
        if product is None:
            raise NotFound("Товар більше недоступний", extra={"product_id": request.product_id})
        price = line_price(product, request.qty, master=master)
        if require_available and not price.available:
            raise OutOfStock(f"Недостатньо «{product.name}» на складі",
                             extra={"product_id": product.id, "sku": product.sku})
        lines.append(PricedLine(price=price, group_label=request.group_label))
    return lines


def _apply_totals(order: Order) -> None:
    items = list(order.items.all())
    order.subtotal_kop = sum(item.total_kop for item in items)
    order.total_kop = order.subtotal_kop + (order.delivery_kop or 0)
    order.weight_kg = sum((item.weight_kg for item in items), Decimal("0"))


@transaction.atomic
def create_order(*, customer: Customer, delivery_method: str, delivery: dict[str, Any],
                 payment_method: str, lines: list[PricedLine], delivery_kop: int | None = None,
                 estimate_id: int | None = None, idempotency_key: str | None = None,
                 customer_id: int | None = None, actor=None) -> Order:
    if not lines:
        raise DomainError("Замовлення без товарів", code="empty_order")
    payment_status = (PaymentStatus.ON_DELIVERY if payment_method == PaymentMethod.COD
                      else PaymentStatus.AWAITING)
    order = Order.objects.create(
        customer_name=customer.name, phone=customer.phone, email=customer.email,
        comment=customer.comment, delivery_method=delivery_method, delivery=delivery,
        payment_method=payment_method, payment_status=payment_status,
        delivery_kop=delivery_kop, estimate_id=estimate_id, idempotency_key=idempotency_key,
        customer_id=customer_id,
    )
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order, product_id=line.price.product_id, sku=line.price.sku,
            name=line.price.name, unit=line.price.unit, qty=line.price.qty,
            qty_base=line.price.base_qty, price_kop=line.price.price_kop,
            total_kop=line.price.total_kop, weight_kg=line.price.weight_kg,
            group_label=line.group_label,
        )
        for line in lines
    ])
    order.number = f"KER-{order.pk:06d}"
    _apply_totals(order)
    order.save()
    OrderEvent.objects.create(order=order, from_status="", to_status=OrderStatus.NEW,
                              actor=actor)
    return order


def _lock(order_id: int) -> Order:
    order = Order.objects.select_for_update().filter(pk=order_id).first()
    if order is None:
        raise NotFound("Замовлення не знайдено")
    return order


@transaction.atomic
def transition(order_id: int, target: str, *, actor=None, comment: str = "") -> Order:
    order = _lock(order_id)
    current = order.status
    if not can_transition(current, target):
        raise InvalidTransition(
            f"Не можна перевести замовлення зі статусу «{OrderStatus(current).label}» "
            f"у «{OrderStatus(target).label}»"
        )
    now = timezone.now()
    items = list(order.items.select_for_update())

    if target == OrderStatus.CONFIRMED:
        for item in items:
            if item.product_id:
                item.reserved_qty = catalog_services.reserve(item.product_id, item.qty_base)
                item.save(update_fields=["reserved_qty"])
        order.confirmed_at = now
    elif target == OrderStatus.SHIPPED:
        if (order.payment_method == PaymentMethod.ONLINE
                and order.payment_status != PaymentStatus.PAID):
            raise PaymentRequired()
        for item in items:
            if item.product_id and item.reserved_qty:
                catalog_services.write_off(item.product_id, item.reserved_qty)
                item.reserved_qty = Decimal("0")
                item.save(update_fields=["reserved_qty"])
        order.shipped_at = now
    elif target == OrderStatus.COMPLETED:
        order.completed_at = now
    elif target == OrderStatus.CANCELLED:
        if current in RESERVED_STATUSES:
            for item in items:
                if item.product_id and item.reserved_qty:
                    catalog_services.release(item.product_id, item.reserved_qty)
                    item.reserved_qty = Decimal("0")
                    item.save(update_fields=["reserved_qty"])
        order.cancelled_at = now
        bus.publish(events.ORDER_CANCELLED, {"order_id": order.pk})

    order.status = target
    order.save()
    OrderEvent.objects.create(order=order, from_status=current, to_status=target, actor=actor,
                              comment=comment[:255])
    bus.publish(events.ORDER_STATUS_CHANGED,
                {"order_id": order.pk, "from": current, "to": target})
    return order


@transaction.atomic
def mark_paid(order_id: int, amount_kop: int) -> Order:
    order = _lock(order_id)
    if order.payment_status == PaymentStatus.PAID:
        return order
    if amount_kop != order.total_kop or order.status == OrderStatus.CANCELLED:
        order.needs_review = True
        order.save(update_fields=["needs_review", "updated_at"])
        bus.publish(events.ORDER_PAYMENT_MISMATCH,
                    {"order_id": order.pk, "amount_kop": amount_kop})
        return order
    order.payment_status = PaymentStatus.PAID
    order.paid_at = timezone.now()
    order.save(update_fields=["payment_status", "paid_at", "updated_at"])
    bus.publish(events.ORDER_PAID, {"order_id": order.pk})
    return order


@transaction.atomic
def mark_refunded(order_id: int) -> Order:
    order = _lock(order_id)
    if order.payment_status != PaymentStatus.REFUNDED:
        order.payment_status = PaymentStatus.REFUNDED
        order.save(update_fields=["payment_status", "updated_at"])
        bus.publish(events.ORDER_REFUNDED, {"order_id": order.pk})
    return order


def _ensure_editable(order: Order) -> None:
    if order.status != OrderStatus.NEW or order.payment_status == PaymentStatus.PAID:
        raise DomainError("Позиції можна змінювати лише в новому неоплаченому замовленні")


def claim_guest_orders(payload: dict[str, Any]) -> None:
    """customer.logged_in handler: guest orders with the same phone number
    move into the customer's account."""
    Order.objects.filter(customer__isnull=True, phone=payload["phone"]).update(
        customer_id=payload["customer_id"])


@transaction.atomic
def reprice(order_id: int) -> Order:
    """Recalculates lines and totals after a manager's edits."""
    order = _lock(order_id)
    _ensure_editable(order)
    items = list(order.items.select_related("product__tile_spec"))
    for item in items:
        if item.product is None:
            continue
        master = bool(order.customer_id and order.customer and order.customer.is_master)
        price = line_price(item.product, item.qty, master=master)
        item.qty_base = price.base_qty
        item.price_kop = price.price_kop
        item.total_kop = price.total_kop
        item.weight_kg = price.weight_kg
        item.save(update_fields=["qty_base", "price_kop", "total_kop", "weight_kg"])
    _apply_totals(order)
    order.save()
    return order


@transaction.atomic
def set_delivery_cost(order_id: int, delivery_kop: int | None) -> Order:
    order = _lock(order_id)
    if order.payment_status == PaymentStatus.PAID:
        raise DomainError("Замовлення вже оплачене, суму змінити не можна")
    order.delivery_kop = delivery_kop
    _apply_totals(order)
    order.save()
    return order


@transaction.atomic
def mark_reminded(order_id: int) -> None:
    order = _lock(order_id)
    order.reminded_at = timezone.now()
    order.save(update_fields=["reminded_at"])
    bus.publish(events.ORDER_UNCONFIRMED_REMINDER, {"order_id": order.pk})
