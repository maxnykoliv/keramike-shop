from rest_framework import serializers

from apps.core.phone import InvalidPhone, normalize_phone
from apps.customers.models import Customer, CustomerAddress


class PhoneField(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        try:
            return normalize_phone(value)
        except InvalidPhone as exc:
            raise serializers.ValidationError(str(exc)) from exc


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "phone", "name", "email", "is_master", "telegram_username",
                  "created_at"]
        read_only_fields = ["id", "phone", "is_master", "telegram_username", "created_at"]


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerAddress
        fields = ["id", "label", "delivery_method", "city_ref", "city_name", "warehouse_ref",
                  "warehouse_name", "address", "is_default"]

    def validate(self, attrs):
        method = attrs.get("delivery_method", getattr(self.instance, "delivery_method", None))
        merged = {**({} if self.instance is None else {
            f: getattr(self.instance, f) for f in ("city_ref", "warehouse_ref", "address")
        }), **attrs}
        if method == CustomerAddress.Method.NOVA_POSHTA and not (
            merged.get("city_ref") and merged.get("warehouse_ref")
        ):
            raise serializers.ValidationError({"warehouse_ref": "Оберіть місто й відділення"})
        if method == CustomerAddress.Method.LOCAL and not merged.get("address"):
            raise serializers.ValidationError({"address": "Вкажіть адресу"})
        return attrs


class LoginResultSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    customer = CustomerSerializer()


class TelegramStartSerializer(serializers.Serializer):
    login_id = serializers.UUIDField()
    poll_secret = serializers.CharField()
    bot_url = serializers.CharField()
    expires_at = serializers.DateTimeField()


class TelegramPollSerializer(serializers.Serializer):
    login_id = serializers.UUIDField()
    poll_secret = serializers.CharField(max_length=64)


class TelegramPollResultSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=["pending", "awaiting_contact", "confirmed", "expired"])
    token = serializers.CharField(required=False)
    expires_at = serializers.DateTimeField(required=False)
    customer = CustomerSerializer(required=False)


class CodeRequestSerializer(serializers.Serializer):
    phone = PhoneField(max_length=32)
    channel = serializers.CharField(max_length=20)


class CodeVerifySerializer(serializers.Serializer):
    phone = PhoneField(max_length=32)
    code = serializers.RegexField(r"^\s*\d{6}\s*$")
