"""Checkout: cart → order → payment.

A separate app breaks the orders ↔ payments cycle: orders know nothing about payments.
"""

from dataclasses import dataclass
from typing import Any

import structlog
from django.db import IntegrityError, transaction

from apps.cart import selectors as cart_selectors
from apps.cart import services as cart_services
from apps.core import events as bus
from apps.core.exceptions import EmptyCart, ProviderUnavailable
from apps.customers.models import Customer
from apps.delivery import services as delivery_services
from apps.orders import events as order_events
from apps.orders import selectors as order_selectors
from apps.orders import services as order_services
from apps.orders.models import Order
from apps.payments import selectors as payment_selectors
from apps.payments import services as payment_services

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CheckoutResult:
    order: Order
    payment_url: str | None
    payment_retry: bool = False


def _existing(key: str | None) -> CheckoutResult | None:
    if not key:
        return None
    order = order_selectors.find_by_idempotency_key(key)
    if order is None:
        return None
    payment = payment_selectors.latest_payment(order.pk)
    return CheckoutResult(order=order, payment_url=payment.payment_url if payment else None)


def _create(cart_token: str, customer: order_services.Customer, delivery_method: str,
            delivery: dict[str, Any], payment_method: str, quote_id: str | None,
            idempotency_key: str | None, account: Customer | None) -> Order:
    with transaction.atomic():
        cart = cart_selectors.get_cart_for_update(cart_token)
        items = list(cart.items.all())
        if not items:
            raise EmptyCart()
        lines = order_services.build_lines([
            order_services.LineRequest(product_id=item.product_id, qty=item.qty,
                                       group_label=item.group_label)
            for item in items
        ], master=bool(account and account.is_master))
        estimate_ids = {item.estimate_id for item in items if item.estimate_id}
        order = order_services.create_order(
            customer=customer,
            delivery_method=delivery_method,
            delivery=delivery,
            payment_method=payment_method,
            lines=lines,
            delivery_kop=delivery_services.cached_quote(quote_id, method=delivery_method,
                                                        cart_token=cart_token),
            estimate_id=next(iter(estimate_ids)) if len(estimate_ids) == 1 else None,
            idempotency_key=idempotency_key,
            customer_id=account.pk if account else None,
        )
        cart_services.close(cart)
        bus.publish(order_events.ORDER_CREATED, {"order_id": order.pk})
    return order


def place_order(*, cart_token: str, customer: order_services.Customer, delivery_method: str,
                delivery: dict[str, Any], payment_method: str, quote_id: str | None = None,
                idempotency_key: str | None = None,
                account: Customer | None = None) -> CheckoutResult:
    """account is the logged-in customer: the order joins their account, master prices apply."""
    existing = _existing(idempotency_key)
    if existing:
        return existing
    try:
        order = _create(cart_token, customer, delivery_method, delivery, payment_method,
                        quote_id, idempotency_key, account)
    except IntegrityError:
        # A concurrent request with the same key got there first.
        existing = _existing(idempotency_key)
        if existing:
            return existing
        raise

    # Call the payment provider only after the order is committed.
    try:
        payment = payment_services.start_payment(order)
    except ProviderUnavailable:
        return CheckoutResult(order=order, payment_url=None, payment_retry=True)
    return CheckoutResult(order=order, payment_url=payment.payment_url if payment else None)


def retry_payment(order_token: str) -> str:
    order = order_selectors.get_by_token(order_token)
    payment = payment_services.start_payment(order)
    if payment is None:
        raise ProviderUnavailable("Для цього замовлення онлайн-оплата не передбачена")
    return payment.payment_url
