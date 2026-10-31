from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin
from unfold.decorators import action

from apps.core.exceptions import DomainError
from apps.core.money import format_uah
from apps.leads import services
from apps.leads.models import Lead


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ("name", "phone", "status", "estimate_total", "manager", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "phone", "estimate__public_code")
    readonly_fields = ("estimate", "order", "estimate_lines", "created_at")
    fields = ("name", "phone", "comment", "status", "manager", "estimate", "estimate_lines",
              "order", "created_at")
    actions_detail = ["convert"]

    @admin.display(description="Сума кошторису")
    def estimate_total(self, obj: Lead) -> str:
        return format_uah(obj.estimate.total_kop) if obj.estimate else "—"

    @admin.display(description="Кошторис")
    def estimate_lines(self, obj: Lead) -> str:
        if not obj.estimate:
            return "—"
        return "; ".join(
            f"{line['name']}: {line['quantity']} → {format_uah(line['total_kop'])}"
            for line in obj.estimate.result["lines"]
        )

    def has_add_permission(self, request) -> bool:
        return False

    def has_convert_permission(self, request, object_id=None) -> bool:
        if not request.user.has_perm("leads.change_lead") or object_id is None:
            return False
        return Lead.objects.filter(pk=object_id, order__isnull=True,
                                   estimate__isnull=False).exists()

    @action(description="Перетворити на замовлення", url_path="convert",
            permissions=["convert"])
    def convert(self, request, object_id):
        try:
            order = services.convert_to_order(int(object_id), actor=request.user)
        except DomainError as exc:
            messages.error(request, exc.message)
            return redirect(reverse("admin:leads_lead_change", args=[object_id]))
        messages.success(request, f"Створено замовлення {order.number}")
        return redirect(reverse("admin:orders_order_change", args=[order.pk]))
