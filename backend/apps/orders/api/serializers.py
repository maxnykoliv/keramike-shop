from rest_framework import serializers

from apps.core.money import format_uah
from apps.orders.models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["product_id", "sku", "name", "unit", "qty", "qty_base", "price_kop",
                  "total_kop", "group_label"]


class PublicOrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    status_label = serializers.CharField(source="get_status_display")
    payment_status_label = serializers.CharField(source="get_payment_status_display")
    total_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["number", "public_token", "status", "status_label", "payment_method",
                  "payment_status", "payment_status_label", "delivery_method", "subtotal_kop",
                  "delivery_kop", "total_kop", "total_display", "weight_kg", "items",
                  "created_at"]

    def get_total_display(self, obj: Order) -> str:
        return format_uah(obj.total_kop)
