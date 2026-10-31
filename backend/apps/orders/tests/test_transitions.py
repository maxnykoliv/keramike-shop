from decimal import Decimal

import pytest

from apps.core.exceptions import InvalidTransition, OutOfStock, PaymentRequired
from apps.orders import services
from apps.orders.models import OrderEvent
from apps.orders.state import OrderStatus

pytestmark = pytest.mark.django_db


def create(product, *, qty=3, payment_method="cod"):
    return services.create_order(
        customer=services.Customer(name="Іван", phone="+380671234567"),
        delivery_method="pickup", delivery={}, payment_method=payment_method,
        lines=services.build_lines([services.LineRequest(product_id=product.id, qty=qty)]),
        delivery_kop=0,
    )


def test_full_cycle_reserves_and_writes_off(tile):
    order = create(tile)
    services.transition(order.id, OrderStatus.CONFIRMED)
    tile.refresh_from_db()
    assert tile.reserved_qty == Decimal("4.320")

    services.transition(order.id, OrderStatus.PACKED)
    services.transition(order.id, OrderStatus.SHIPPED)
    tile.refresh_from_db()
    assert (tile.stock_qty, tile.reserved_qty) == (Decimal("95.680"), Decimal("0"))

    services.transition(order.id, OrderStatus.COMPLETED)
    statuses = list(OrderEvent.objects.filter(order=order).values_list("to_status", flat=True))
    assert statuses == ["new", "confirmed", "packed", "shipped", "completed"]


def test_cancel_releases_reservation(tile):
    order = create(tile)
    services.transition(order.id, OrderStatus.CONFIRMED)
    services.transition(order.id, OrderStatus.CANCELLED)
    tile.refresh_from_db()
    assert tile.reserved_qty == Decimal("0")


def test_invalid_transition(tile):
    order = create(tile)
    with pytest.raises(InvalidTransition):
        services.transition(order.id, OrderStatus.SHIPPED)


def test_online_order_cannot_ship_unpaid(tile):
    order = create(tile, payment_method="online")
    services.transition(order.id, OrderStatus.CONFIRMED)
    services.transition(order.id, OrderStatus.PACKED)
    with pytest.raises(PaymentRequired):
        services.transition(order.id, OrderStatus.SHIPPED)
    services.mark_paid(order.id, order.total_kop)
    services.transition(order.id, OrderStatus.SHIPPED)


def test_confirm_fails_when_stock_sold_out(tile):
    first = create(tile, qty=40)  # 57,6 м²
    second = create(tile, qty=40)
    services.transition(first.id, OrderStatus.CONFIRMED)
    with pytest.raises(OutOfStock):
        services.transition(second.id, OrderStatus.CONFIRMED)
    second.refresh_from_db()
    assert second.status == OrderStatus.NEW


def test_mark_paid_mismatch_flags_order(tile):
    order = create(tile, payment_method="online")
    services.mark_paid(order.id, order.total_kop - 1)
    order.refresh_from_db()
    assert order.needs_review is True
    assert order.payment_status == "awaiting"


def test_reprice_after_qty_change(tile):
    order = create(tile)
    item = order.items.get()
    item.qty = 4
    item.save()
    order = services.reprice(order.id)
    assert order.subtotal_kop == 4 * 144 * 650
    assert order.total_kop == order.subtotal_kop
