from django.contrib import admin, messages
from import_export.admin import ImportExportModelAdmin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from apps.catalog import services
from apps.catalog.models import (
    Category,
    Collection,
    Manufacturer,
    MaterialSpec,
    Product,
    ProductImage,
    ProductRelation,
    TileSpec,
)
from apps.catalog.resources import ProductResource
from apps.core.money import format_uah
from apps.core.roles import is_owner

PRICE_FIELDS = ("price_kop", "old_price_kop", "master_price_kop")


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "parent", "sort", "is_active")
    list_editable = ("sort", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Manufacturer)
class ManufacturerAdmin(ModelAdmin):
    list_display = ("name", "country")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Collection)
class CollectionAdmin(ModelAdmin):
    list_display = ("name", "manufacturer")
    list_filter = ("manufacturer",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "manufacturer__name")
    autocomplete_fields = ("manufacturer",)


class TileSpecInline(StackedInline):
    model = TileSpec
    can_delete = False
    extra = 0


class MaterialSpecInline(StackedInline):
    model = MaterialSpec
    can_delete = False
    extra = 0


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 0
    fields = ("image", "kind", "alt", "sort")


class ProductRelationInline(TabularInline):
    model = ProductRelation
    fk_name = "product"
    extra = 0
    autocomplete_fields = ("related",)


@admin.register(Product)
class ProductAdmin(SimpleHistoryAdmin, ImportExportModelAdmin, ModelAdmin):
    resource_classes = [ProductResource]
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ("name", "sku", "kind", "status", "price", "available", "stock_status")
    list_filter = ("status", "kind", "stock_status", "category", "collection__manufacturer")
    search_fields = ("name", "sku")
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("collection",)
    list_select_related = ("category",)
    readonly_fields = ("reserved_qty", "created_at", "updated_at")
    inlines = [TileSpecInline, MaterialSpecInline, ProductImageInline, ProductRelationInline]
    actions = ["make_active", "make_hidden"]
    fieldsets = (
        (None, {"fields": ("name", "sku", "slug", "kind", "category", "collection", "status")}),
        ("Ціна", {"fields": ("unit", "price_kop", "old_price_kop", "master_price_kop")}),
        ("Склад", {"fields": ("stock_qty", "reserved_qty", "stock_status", "weight_kg")}),
        ("Опис і SEO", {"fields": ("description", "seo_title", "seo_description")}),
        ("Дати", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Ціна", ordering="price_kop")
    def price(self, obj: Product) -> str:
        return format_uah(obj.price_kop)

    @admin.display(description="Доступно")
    def available(self, obj: Product) -> str:
        return f"{obj.available_qty} {obj.get_unit_display()}"

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        if not is_owner(request.user):
            fields = (*fields, *PRICE_FIELDS)
        return fields

    def has_import_permission(self, request) -> bool:
        return is_owner(request.user)

    @admin.action(description="Опублікувати")
    def make_active(self, request, queryset) -> None:
        for product in queryset:
            services.set_status(product, Product.Status.ACTIVE)
        messages.success(request, f"Опубліковано: {queryset.count()}")

    @admin.action(description="Приховати")
    def make_hidden(self, request, queryset) -> None:
        for product in queryset:
            services.set_status(product, Product.Status.HIDDEN)
        messages.success(request, f"Приховано: {queryset.count()}")
