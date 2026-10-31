"""Імпорт і експорт товарів через Excel. Ключ рядка — артикул."""

from decimal import Decimal, InvalidOperation

from django.utils.text import slugify
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget

from apps.catalog.models import Category, Collection, Product, TileSpec
from apps.core import events
from apps.core.money import kop_to_uah, uah_to_kop

TILE_FIELDS = ["width_mm", "height_mm", "thickness_mm", "m2_per_pack", "pcs_per_pack",
               "pack_weight_kg", "material", "surface", "color"]


def _decimal(value) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"Некоректне число: {value}") from exc


def _list(value) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in str(value).split(",") if item.strip()]


class ProductResource(resources.ModelResource):
    category = fields.Field(column_name="category", attribute="category",
                            widget=ForeignKeyWidget(Category, field="slug"))
    collection = fields.Field(column_name="collection", attribute="collection",
                              widget=ForeignKeyWidget(Collection, field="slug"))
    price_uah = fields.Field(column_name="price_uah")
    master_price_uah = fields.Field(column_name="master_price_uah")
    width_mm = fields.Field(column_name="width_mm")
    height_mm = fields.Field(column_name="height_mm")
    thickness_mm = fields.Field(column_name="thickness_mm")
    m2_per_pack = fields.Field(column_name="m2_per_pack")
    pcs_per_pack = fields.Field(column_name="pcs_per_pack")
    pack_weight_kg = fields.Field(column_name="pack_weight_kg")
    material = fields.Field(column_name="material")
    surface = fields.Field(column_name="surface")
    color = fields.Field(column_name="color")
    applications = fields.Field(column_name="applications")
    rooms = fields.Field(column_name="rooms")

    class Meta:
        model = Product
        import_id_fields = ["sku"]
        fields = ["sku", "name", "slug", "kind", "category", "collection", "status", "unit",
                  "price_uah", "master_price_uah", "stock_qty", "stock_status", "weight_kg",
                  "description",
                  *TILE_FIELDS, "applications", "rooms"]
        export_order = fields
        skip_unchanged = True
        report_skipped = False
        use_transactions = True

    def before_save_instance(self, instance: Product, row, **kwargs) -> None:
        price = _decimal(row.get("price_uah"))
        if price is None:
            raise ValueError("Ціна price_uah обов'язкова")
        instance.price_kop = uah_to_kop(price)
        master_price = _decimal(row.get("master_price_uah"))
        instance.master_price_kop = None if master_price is None else uah_to_kop(master_price)
        if not instance.slug:
            instance.slug = slugify(f"{instance.name}-{instance.sku}", allow_unicode=False) or (
                slugify(instance.sku)
            )

    def after_save_instance(self, instance: Product, row, **kwargs) -> None:
        if not row.get("width_mm"):
            return
        TileSpec.objects.update_or_create(
            product=instance,
            defaults={
                "width_mm": int(row["width_mm"]),
                "height_mm": int(row["height_mm"]),
                "thickness_mm": int(row.get("thickness_mm") or 8),
                "m2_per_pack": _decimal(row.get("m2_per_pack")),
                "pcs_per_pack": int(row["pcs_per_pack"]) if row.get("pcs_per_pack") else None,
                "pack_weight_kg": _decimal(row.get("pack_weight_kg")),
                "material": row.get("material") or TileSpec.Material.CERAMIC,
                "surface": row.get("surface") or "",
                "color": row.get("color") or "",
                "applications": _list(row.get("applications")),
                "rooms": _list(row.get("rooms")),
            },
        )

    def after_import(self, dataset, result, **kwargs) -> None:
        super().after_import(dataset, result, **kwargs)
        if kwargs.get("dry_run") or result.has_errors():
            return
        totals = result.totals
        events.publish("catalog.import_finished", {
            "new": totals.get("new", 0),
            "updated": totals.get("update", 0),
            "errors": totals.get("error", 0),
        })

    def dehydrate_price_uah(self, product: Product) -> str:
        return str(kop_to_uah(product.price_kop))

    def dehydrate_master_price_uah(self, product: Product) -> str:
        if product.master_price_kop is None:
            return ""
        return str(kop_to_uah(product.master_price_kop))

    def _spec(self, product: Product, name: str):
        spec = getattr(product, "tile_spec", None)
        if spec is None:
            return ""
        value = getattr(spec, name)
        if isinstance(value, list):
            return ",".join(value)
        return "" if value is None else value

    def dehydrate_width_mm(self, product): return self._spec(product, "width_mm")
    def dehydrate_height_mm(self, product): return self._spec(product, "height_mm")
    def dehydrate_thickness_mm(self, product): return self._spec(product, "thickness_mm")
    def dehydrate_m2_per_pack(self, product): return self._spec(product, "m2_per_pack")
    def dehydrate_pcs_per_pack(self, product): return self._spec(product, "pcs_per_pack")
    def dehydrate_pack_weight_kg(self, product): return self._spec(product, "pack_weight_kg")
    def dehydrate_material(self, product): return self._spec(product, "material")
    def dehydrate_surface(self, product): return self._spec(product, "surface")
    def dehydrate_color(self, product): return self._spec(product, "color")
    def dehydrate_applications(self, product): return self._spec(product, "applications")
    def dehydrate_rooms(self, product): return self._spec(product, "rooms")
