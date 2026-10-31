from rest_framework import serializers

from apps.customers.api.serializers import PhoneField
from apps.orders.state import DeliveryMethod, PaymentMethod


class DeliverySerializer(serializers.Serializer):
    city_ref = serializers.CharField(max_length=64, required=False, allow_blank=True)
    city_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    warehouse_ref = serializers.CharField(max_length=64, required=False, allow_blank=True)
    warehouse_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address = serializers.CharField(max_length=500, required=False, allow_blank=True)


class CheckoutSerializer(serializers.Serializer):
    cart_token = serializers.CharField(max_length=64)
    name = serializers.CharField(max_length=150)
    phone = PhoneField(max_length=32)
    email = serializers.EmailField(required=False, allow_blank=True, default="")
    comment = serializers.CharField(max_length=2000, required=False, allow_blank=True,
                                    default="")
    delivery_method = serializers.ChoiceField(choices=DeliveryMethod.choices)
    delivery = DeliverySerializer(required=False, default=dict)
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)
    quote_id = serializers.CharField(max_length=40, required=False, allow_blank=True)
    captcha = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        delivery = attrs.get("delivery") or {}
        method = attrs["delivery_method"]
        if method == DeliveryMethod.NOVA_POSHTA and not (
            delivery.get("city_ref") and delivery.get("warehouse_ref")
        ):
            raise serializers.ValidationError({"delivery": "Оберіть місто й відділення"})
        if method == DeliveryMethod.LOCAL and not delivery.get("address"):
            raise serializers.ValidationError({"delivery": "Вкажіть адресу доставки"})
        return attrs
