from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin
from unfold.decorators import action

from apps.calc import services
from apps.calc.models import CalcSettings, Estimate, LaborRate
from apps.core.exceptions import DomainError
from apps.core.money import format_uah
from apps.core.roles import is_owner


@admin.register(CalcSettings)
class CalcSettingsAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ("version", "status", "published_at", "published_by")
    list_filter = ("status",)
    readonly_fields = ("version", "status", "published_by", "published_at", "sample_result")
    autocomplete_fields = ("glue_product", "grout_product", "primer_product",
                           "waterproofing_product")
    actions_detail = ["publish", "clone"]
    fieldsets = (
        (None, {"fields": ("version", "status", "published_by", "published_at")}),
        ("Коефіцієнти", {"fields": ("waste_by_layout", "glue_kg_per_m2", "grout_density",
                                    "primer_l_per_m2", "waterproofing_kg_per_m2")}),
        ("Матеріали за замовчуванням", {"fields": ("glue_product", "grout_product",
                                                   "primer_product", "waterproofing_product")}),
        ("Тестовий приклад: ванна 2,0×1,7 м, плитка 60×60", {"fields": ("sample_result",)}),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status != CalcSettings.Status.DRAFT:
            return [f.name for f in self.model._meta.fields] + ["sample_result"]
        return super().get_readonly_fields(request, obj)

    def has_change_permission(self, request, obj=None) -> bool:
        return is_owner(request.user)

    def has_add_permission(self, request) -> bool:
        return is_owner(request.user)

    def has_delete_permission(self, request, obj=None) -> bool:
        return is_owner(request.user) and bool(obj) and obj.status == CalcSettings.Status.DRAFT

    @admin.display(description="Результат")
    def sample_result(self, obj: CalcSettings) -> str:
        if not obj.pk:
            return "Збережіть чернетку, щоб побачити розрахунок"
        try:
            result = services.preview(obj)
        except DomainError as exc:
            return exc.message
        rows = format_html_join(
            "", "<tr><td>{}</td><td>{} → {}</td><td>{}</td></tr>",
            ((line["name"], line["quantity_base"], line["quantity"],
              format_uah(line["total_kop"])) for line in result["lines"]),
        )
        return format_html("<table>{}<tr><td><b>Разом</b></td><td></td><td><b>{}</b></td></tr>"
                           "</table>", rows, format_uah(result["total_kop"]))

    def has_publish_permission(self, request, object_id=None) -> bool:
        return is_owner(request.user)

    def has_clone_permission(self, request, object_id=None) -> bool:
        return is_owner(request.user)

    @action(description="Опублікувати версію", url_path="publish", permissions=["publish"])
    def publish(self, request, object_id):
        try:
            services.publish_settings(CalcSettings.objects.get(pk=object_id), request.user)
            messages.success(request, "Версію опубліковано, калькулятор уже рахує за нею")
        except DomainError as exc:
            messages.error(request, exc.message)
        return redirect(reverse("admin:calc_calcsettings_change", args=[object_id]))

    @action(description="Створити чернетку на основі", url_path="clone", permissions=["clone"])
    def clone(self, request, object_id):
        draft = services.clone_as_draft(CalcSettings.objects.get(pk=object_id))
        messages.success(request, f"Створено чернетку версії {draft.version}")
        return redirect(reverse("admin:calc_calcsettings_change", args=[draft.pk]))


@admin.register(LaborRate)
class LaborRateAdmin(SimpleHistoryAdmin, ModelAdmin):
    list_display = ("surface", "size_class", "price_kop_per_m2", "price")
    list_editable = ("price_kop_per_m2",)

    @admin.display(description="Ціна за м²")
    def price(self, obj: LaborRate) -> str:
        return format_uah(obj.price_kop_per_m2)

    def has_change_permission(self, request, obj=None) -> bool:
        return is_owner(request.user)

    def has_add_permission(self, request) -> bool:
        return is_owner(request.user)


@admin.register(Estimate)
class EstimateAdmin(ModelAdmin):
    list_display = ("public_code", "total", "source", "created_at")
    list_filter = ("source",)
    search_fields = ("public_code",)
    readonly_fields = ("public_code", "input", "result", "settings", "total_kop", "source",
                       "pdf", "created_at")

    @admin.display(description="Разом", ordering="total_kop")
    def total(self, obj: Estimate) -> str:
        return format_uah(obj.total_kop)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
