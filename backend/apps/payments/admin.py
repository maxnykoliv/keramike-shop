from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.money import format_uah
from apps.payments.models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("reference", "order", "provider", "status", "amount", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("reference", "provider_payment_id", "order__number")
    readonly_fields = [f.name for f in Payment._meta.fields]

    @admin.display(description="Сума", ordering="amount_kop")
    def amount(self, obj: Payment) -> str:
        return format_uah(obj.amount_kop)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
