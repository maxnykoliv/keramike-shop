from dataclasses import dataclass
from decimal import Decimal

from django.utils import timezone

from apps.cart.models import Cart
from apps.catalog.selectors import LinePrice, line_price
from apps.core.exceptions import NotFound


@dataclass(frozen=True)
class CartLine:
    item_id: int
    group_label: str
    price: LinePrice


@dataclass(frozen=True)
class CartView:
    cart: Cart
    lines: list[CartLine]
    subtotal_kop: int
    weight_kg: Decimal

    @property
    def unavailable(self) -> list[CartLine]:
        return [line for line in self.lines if not line.price.available]


def _open_carts():
    return Cart.objects.filter(closed_at__isnull=True, expires_at__gt=timezone.now())


def get_cart(token: str) -> Cart:
    cart = _open_carts().filter(token=token).first()
    if cart is None:
        raise NotFound("Кошик не знайдено або він уже оформлений")
    return cart


def get_cart_for_update(token: str) -> Cart:
    cart = _open_carts().select_for_update().filter(token=token).first()
    if cart is None:
        raise NotFound("Кошик не знайдено або він уже оформлений")
    return cart


def cart_view(cart: Cart, *, master: bool = False) -> CartView:
    """Кошик з актуальними цінами з каталогу, вагою і перевіркою залишків."""
    items = cart.items.select_related("product__tile_spec", "product__material_spec")
    lines = [
        CartLine(item_id=item.id, group_label=item.group_label,
                 price=line_price(item.product, item.qty, master=master))
        for item in items
    ]
    return CartView(
        cart=cart,
        lines=lines,
        subtotal_kop=sum(line.price.total_kop for line in lines),
        weight_kg=sum((line.price.weight_kg for line in lines), Decimal("0")),
    )
