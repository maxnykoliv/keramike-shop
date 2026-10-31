from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import action

from apps.core.exceptions import DomainError
from apps.delivery import services
from apps.delivery.models import DeliverySettings, Shipment


@admin.register(Shipment)
class ShipmentAdmin(ModelAdmin):
    list_display = ("order", "carrier", "status", "ttn", "created_at")
    list_filter = ("status", "carrier")
    search_fields = ("ttn", "order__number")
    readonly_fields = ("ttn", "cost_kop", "raw", "created_at")
    autocomplete_fields = ("order",)
    actions_detail = ["create_ttn"]

    def has_create_ttn_permission(self, request, object_id=None) -> bool:
        if not request.user.has_perm("delivery.change_shipment") or object_id is None:
            return False
        return Shipment.objects.filter(pk=object_id, status=Shipment.Status.DRAFT,
                                       carrier=Shipment.Carrier.NOVA_POSHTA).exists()

    @action(description="Створити ТТН", url_path="create-ttn", permissions=["create_ttn"])
    def create_ttn(self, request, object_id):
        try:
            shipment = services.create_ttn(int(object_id))
            messages.success(request, f"ТТН {shipment.ttn} створено")
        except DomainError as exc:
            messages.error(request, exc.message)
        return redirect(reverse("admin:delivery_shipment_change", args=[object_id]))


@admin.register(DeliverySettings)
class DeliverySettingsAdmin(ModelAdmin):
    def has_add_permission(self, request) -> bool:
        return not DeliverySettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
