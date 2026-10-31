from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.calc.models import Estimate
from apps.cart.models import CART_TTL, Cart, CartItem
from apps.catalog.models import Product
from apps.core.exceptions import DomainError, NotFound

MAX_QTY = 10_000


def create_cart() -> Cart:
    return Cart.objects.create()


def _touch(cart: Cart) -> None:
    Cart.objects.filter(pk=cart.pk).update(expires_at=timezone.now() + CART_TTL)


def _check_product(product_id: int) -> Product:
    product = Product.objects.filter(pk=product_id, status=Product.Status.ACTIVE).first()
    if product is None:
        raise NotFound("Товар недоступний", field="product_id")
    return product


@transaction.atomic
def add_item(cart: Cart, product_id: int, qty: int, *, group_label: str = "",
             estimate: Estimate | None = None) -> CartItem:
    if qty <= 0 or qty > MAX_QTY:
        raise DomainError("Некоректна кількість", field="qty")
    _check_product(product_id)
    item, created = CartItem.objects.get_or_create(
        cart=cart, product_id=product_id, group_label=group_label,
        defaults={"qty": qty, "estimate": estimate},
    )
    if not created:
        CartItem.objects.filter(pk=item.pk).update(qty=F("qty") + qty)
        item.refresh_from_db()
    _touch(cart)
    return item


def update_item(cart: Cart, item_id: int, qty: int) -> CartItem:
    if qty <= 0 or qty > MAX_QTY:
        raise DomainError("Некоректна кількість", field="qty")
    item = cart.items.filter(pk=item_id).first()
    if item is None:
        raise NotFound("Позицію не знайдено")
    item.qty = qty
    item.save(update_fields=["qty", "updated_at"])
    _touch(cart)
    return item


def remove_item(cart: Cart, item_id: int) -> None:
    deleted, _ = cart.items.filter(pk=item_id).delete()
    if not deleted:
        raise NotFound("Позицію не знайдено")


@transaction.atomic
def add_from_estimate(cart: Cart, estimate: Estimate) -> list[CartItem]:
    """Adds an estimate's products as one group. Labour does not go into the cart."""
    label = f"Кошторис {estimate.public_code}"
    added = []
    for line in estimate.result["lines"]:
        if not line.get("product_id") or line["kind"] == "labor":
            continue
        qty = int(Decimal(line["quantity"]))
        added.append(add_item(cart, line["product_id"], qty, group_label=label,
                              estimate=estimate))
    if not added:
        raise DomainError("У кошторисі немає товарів з каталогу")
    return added


def close(cart: Cart) -> None:
    Cart.objects.filter(pk=cart.pk).update(closed_at=timezone.now())
