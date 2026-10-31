from decimal import Decimal

from apps.calc import engine
from apps.calc.engine.types import CalcSettings as EngineSettings
from apps.calc.models import CalcSettings, Estimate, LaborRate
from apps.catalog.models import Product
from apps.catalog.selectors import effective_price
from apps.core.exceptions import NotFound

MATERIAL_FIELDS = {
    "glue": "glue_product",
    "grout": "grout_product",
    "primer": "primer_product",
    "waterproofing": "waterproofing_product",
}


def active_settings() -> CalcSettings:
    current = (
        CalcSettings.objects.filter(status=CalcSettings.Status.PUBLISHED)
        .select_related(*[f"{field}__material_spec" for field in MATERIAL_FIELDS.values()])
        .first()
    )
    if current is None:
        raise NotFound("Калькулятор ще не налаштований")
    return current


def settings_dict(model: CalcSettings, *, master: bool = False) -> dict:
    """Settings in the engine format, the same as calc-cases/settings.json."""
    labor: dict[str, dict[str, int]] = {
        "floor": {"small": 0, "medium": 0, "large": 0},
        "walls": {"small": 0, "medium": 0, "large": 0},
    }
    for rate in LaborRate.objects.all():
        labor[rate.surface][rate.size_class] = rate.price_kop_per_m2

    materials = {}
    for kind, field in MATERIAL_FIELDS.items():
        product: Product | None = getattr(model, field)
        spec = getattr(product, "material_spec", None) if product else None
        if product is None or spec is None or product.status != Product.Status.ACTIVE:
            continue
        materials[kind] = {
            "name": product.name,
            "pack_size": str(spec.pack_size),
            "price_kop": effective_price(product, master=master),
            "pack_weight_kg": str(product.weight_kg or spec.pack_size),
            "product_id": product.id,
        }

    return {
        "version": model.version,
        "waste_by_layout": model.waste_by_layout,
        "glue_kg_per_m2": model.glue_kg_per_m2,
        "grout_density": str(model.grout_density),
        "primer_l_per_m2": str(model.primer_l_per_m2),
        "waterproofing_kg_per_m2": str(model.waterproofing_kg_per_m2),
        "labor_kop_per_m2": labor,
        "materials": materials,
    }


def engine_settings(model: CalcSettings, *, master: bool = False) -> EngineSettings:
    return engine.settings_from_dict(settings_dict(model, master=master))


def get_estimate(code: str) -> Estimate:
    estimate = Estimate.objects.select_related("settings").filter(public_code=code.upper()).first()
    if estimate is None:
        raise NotFound("Кошторис не знайдено")
    return estimate


def customer_estimates(customer_id: int):
    return Estimate.objects.filter(customer_id=customer_id).order_by("-created_at")


def material_stock(product: Product) -> Decimal | None:
    if product.stock_status == Product.StockStatus.ON_ORDER:
        return None
    return product.available_qty
