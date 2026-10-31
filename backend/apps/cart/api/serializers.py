from rest_framework import serializers

from apps.cart.selectors import CartView
from apps.core.money import format_uah


class AddItemSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    qty = serializers.IntegerField(min_value=1, max_value=10_000)
    group_label = serializers.CharField(max_length=100, required=False, default="")


class UpdateItemSerializer(serializers.Serializer):
    qty = serializers.IntegerField(min_value=1, max_value=10_000)


def cart_to_dict(view: CartView) -> dict:
    return {
        "token": view.cart.token,
        "lines": [
            {
                "id": line.item_id,
                "group_label": line.group_label,
                "product_id": line.price.product_id,
                "sku": line.price.sku,
                "name": line.price.name,
                "qty": line.price.qty,
                "unit": line.price.unit,
                "base_qty": str(line.price.base_qty),
                "price_kop": line.price.price_kop,
                "total_kop": line.price.total_kop,
                "total_display": format_uah(line.price.total_kop),
                "weight_kg": str(line.price.weight_kg),
                "available": line.price.available,
            }
            for line in view.lines
        ],
        "subtotal_kop": view.subtotal_kop,
        "subtotal_display": format_uah(view.subtotal_kop),
        "weight_kg": str(view.weight_kg),
        "has_unavailable": bool(view.unavailable),
    }


class CartLineSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    group_label = serializers.CharField()
    product_id = serializers.IntegerField()
    sku = serializers.CharField()
    name = serializers.CharField()
    qty = serializers.IntegerField()
    unit = serializers.CharField()
    base_qty = serializers.CharField()
    price_kop = serializers.IntegerField()
    total_kop = serializers.IntegerField()
    total_display = serializers.CharField()
    weight_kg = serializers.CharField()
    available = serializers.BooleanField()


class CartSerializer(serializers.Serializer):
    """For the OpenAPI schema only: cart_to_dict builds the response."""

    token = serializers.CharField()
    lines = CartLineSerializer(many=True)
    subtotal_kop = serializers.IntegerField()
    subtotal_display = serializers.CharField()
    weight_kg = serializers.CharField()
    has_unavailable = serializers.BooleanField()
