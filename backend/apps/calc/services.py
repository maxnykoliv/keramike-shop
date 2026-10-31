"""Calculation, saving estimates and publishing settings."""

import secrets
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.calc import engine, selectors
from apps.calc.engine.types import CalcResult
from apps.calc.models import CalcSettings, Estimate
from apps.catalog.models import Product
from apps.catalog.selectors import effective_price, products_by_ids
from apps.core.exceptions import DomainError, InvalidTransition
from apps.customers.models import Customer

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I

SAMPLE_INPUT: dict[str, Any] = {
    "room": "bathroom",
    "surfaces": [{
        "kind": "floor", "length_m": "2.0", "width_m": "1.7", "layout": "straight",
        "joint_mm": "2",
        "tile": {"width_mm": 600, "height_mm": 600, "thickness_mm": 8,
                 "price_kop_per_m2": 65000, "m2_per_pack": "1.44", "pack_weight_kg": "32"},
    }],
    "include": {"glue": True, "grout": True, "primer": True, "waterproofing": True,
                "labor": True},
}


@dataclass(frozen=True)
class Calculation:
    settings: CalcSettings
    resolved_input: dict[str, Any]
    result: CalcResult

    @property
    def result_dict(self) -> dict[str, Any]:
        return engine.result_to_dict(self.result)


def jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [jsonable(item) for item in value]
    return value


def _tile_from_product(product: Product, *, master: bool = False) -> dict[str, Any]:
    spec = product.tile_spec
    return {
        "product_id": product.id,
        "name": product.name,
        "width_mm": spec.width_mm,
        "height_mm": spec.height_mm,
        "thickness_mm": spec.thickness_mm,
        "price_kop_per_m2": effective_price(product, master=master),
        "m2_per_pack": str(spec.effective_m2_per_pack),
        "pack_weight_kg": str(spec.pack_weight_kg) if spec.pack_weight_kg else None,
        "stock_m2": (None if product.stock_status == Product.StockStatus.ON_ORDER
                     else str(product.available_qty)),
        "applications": list(spec.applications),
    }


def resolve_input(payload: dict[str, Any], *, master: bool = False) -> dict[str, Any]:
    """Replaces product_id with the tile's specs and current price from the catalog."""
    payload = jsonable(payload)
    ids = [s["product_id"] for s in payload["surfaces"] if s.get("product_id")]
    products = products_by_ids(ids)
    surfaces = []
    for index, surface in enumerate(payload["surfaces"]):
        surface = dict(surface)
        product_id = surface.pop("product_id", None)
        if product_id:
            product = products.get(product_id)
            if product is None or not hasattr(product, "tile_spec"):
                raise DomainError("Плитку не знайдено або вона недоступна",
                                  field=f"surfaces[{index}].product_id", code="tile_not_found")
            surface["tile"] = _tile_from_product(product, master=master)
        surfaces.append(surface)
    return {**payload, "surfaces": surfaces}


def calculate(payload: dict[str, Any], settings_model: CalcSettings | None = None, *,
              master: bool = False) -> Calculation:
    settings_model = settings_model or selectors.active_settings()
    resolved = resolve_input(payload, master=master)
    try:
        result = engine.calculate(engine.input_from_dict(resolved),
                                  selectors.engine_settings(settings_model, master=master))
    except engine.CalcValidationError as exc:
        raise DomainError(exc.message, field=exc.field, code=exc.code) from exc
    return Calculation(settings=settings_model, resolved_input=resolved, result=result)


def _new_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))


def save_estimate(payload: dict[str, Any], source: str = Estimate.Source.CALCULATOR, *,
                  customer: Customer | None = None, title: str = "") -> Estimate:
    calculation = calculate(payload, master=bool(customer and customer.is_master))
    for _ in range(5):
        try:
            with transaction.atomic():
                return Estimate.objects.create(
                    public_code=_new_code(),
                    input=jsonable(payload),
                    result=calculation.result_dict,
                    settings=calculation.settings,
                    total_kop=calculation.result.total_kop,
                    source=source,
                    customer=customer,
                    title=title,
                )
        except IntegrityError:
            continue
    raise DomainError("Не вдалося зберегти кошторис, спробуйте ще раз")


def recalculate(estimate: Estimate) -> dict[str, Any] | None:
    """Recalculates an estimate at current prices. None if the products are no longer available."""
    try:
        master = bool(estimate.customer and estimate.customer.is_master)
        return calculate(estimate.input, master=master).result_dict
    except DomainError:
        return None


@transaction.atomic
def publish_settings(draft: CalcSettings, user) -> CalcSettings:
    draft = CalcSettings.objects.select_for_update().get(pk=draft.pk)
    if draft.status != CalcSettings.Status.DRAFT:
        raise InvalidTransition("Опублікувати можна лише чернетку")
    preview(draft)
    CalcSettings.objects.filter(status=CalcSettings.Status.PUBLISHED).update(
        status=CalcSettings.Status.ARCHIVED
    )
    draft.status = CalcSettings.Status.PUBLISHED
    draft.published_by = user
    draft.published_at = timezone.now()
    draft.save()
    return draft


def clone_as_draft(source: CalcSettings) -> CalcSettings:
    fields = ["waste_by_layout", "glue_kg_per_m2", "grout_density", "primer_l_per_m2",
              "waterproofing_kg_per_m2", "glue_product_id", "grout_product_id",
              "primer_product_id", "waterproofing_product_id"]
    return CalcSettings.objects.create(**{name: getattr(source, name) for name in fields})


def preview(settings_model: CalcSettings) -> dict[str, Any]:
    """Result of a sample calculation with these settings, to preview changes before publishing."""
    try:
        result = engine.calculate(engine.input_from_dict(SAMPLE_INPUT),
                                  selectors.engine_settings(settings_model))
    except (KeyError, ValueError, ArithmeticError) as exc:
        raise DomainError(f"Налаштування некоректні: {exc!r}", code="invalid_settings") from exc
    return engine.result_to_dict(result)
