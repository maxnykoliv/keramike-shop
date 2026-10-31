"""Перетворення вводу, налаштувань і результату з/у JSON-сумісні словники.

Формат однаковий для API, збережених кошторисів і еталонів calc-cases.
Десяткові числа передаються рядками, гроші — цілими копійками.
"""

from decimal import Decimal
from typing import Any

from apps.calc.engine.types import (
    CalcInput,
    CalcResult,
    CalcSettings,
    Include,
    Layout,
    Material,
    MaterialProduct,
    Opening,
    Room,
    SizeClass,
    Surface,
    SurfaceKind,
    Tile,
)


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))


def tile_from_dict(data: dict[str, Any]) -> Tile:
    return Tile(
        width_mm=int(data["width_mm"]),
        height_mm=int(data["height_mm"]),
        price_kop_per_m2=int(data["price_kop_per_m2"]),
        thickness_mm=int(data.get("thickness_mm") or 8),
        m2_per_pack=_dec(data.get("m2_per_pack")),
        pcs_per_pack=int(data["pcs_per_pack"]) if data.get("pcs_per_pack") else None,
        pack_weight_kg=_dec(data.get("pack_weight_kg")),
        product_id=data.get("product_id"),
        name=data.get("name") or "Плитка",
        stock_m2=_dec(data.get("stock_m2")),
        applications=tuple(data.get("applications") or ()),
    )


def input_from_dict(data: dict[str, Any]) -> CalcInput:
    surfaces = []
    for item in data["surfaces"]:
        surfaces.append(Surface(
            kind=SurfaceKind(item["kind"]),
            tile=tile_from_dict(item["tile"]),
            layout=Layout(item.get("layout") or Layout.STRAIGHT),
            joint_mm=_dec(item.get("joint_mm")) or Decimal("2"),
            length_m=_dec(item.get("length_m")),
            width_m=_dec(item.get("width_m")),
            height_m=_dec(item.get("height_m")),
            area_m2=_dec(item.get("area_m2")),
            openings=tuple(
                Opening(width_m=Decimal(str(o["width_m"])), height_m=Decimal(str(o["height_m"])),
                        count=int(o.get("count", 1)))
                for o in item.get("openings") or []
            ),
        ))
    include = data.get("include") or {}
    return CalcInput(
        room=Room(data.get("room") or Room.OTHER),
        surfaces=tuple(surfaces),
        include=Include(**{key: bool(value) for key, value in include.items()}),
    )


def settings_from_dict(data: dict[str, Any]) -> CalcSettings:
    return CalcSettings(
        version=int(data["version"]),
        waste_by_layout={Layout(k): Decimal(str(v)) for k, v in data["waste_by_layout"].items()},
        glue_kg_per_m2={SizeClass(k): Decimal(str(v)) for k, v in data["glue_kg_per_m2"].items()},
        grout_density=Decimal(str(data["grout_density"])),
        primer_l_per_m2=Decimal(str(data["primer_l_per_m2"])),
        waterproofing_kg_per_m2=Decimal(str(data["waterproofing_kg_per_m2"])),
        labor_kop_per_m2={
            SurfaceKind(kind): {SizeClass(cls): int(price) for cls, price in rates.items()}
            for kind, rates in data["labor_kop_per_m2"].items()
        },
        materials={
            Material(kind): MaterialProduct(
                name=item["name"],
                pack_size=Decimal(str(item["pack_size"])),
                price_kop=int(item["price_kop"]),
                pack_weight_kg=Decimal(str(item.get("pack_weight_kg") or "0")),
                product_id=item.get("product_id"),
            )
            for kind, item in (data.get("materials") or {}).items()
        },
    )


def settings_to_dict(settings: CalcSettings) -> dict[str, Any]:
    return {
        "version": settings.version,
        "waste_by_layout": {k.value: str(v) for k, v in settings.waste_by_layout.items()},
        "glue_kg_per_m2": {k.value: str(v) for k, v in settings.glue_kg_per_m2.items()},
        "grout_density": str(settings.grout_density),
        "primer_l_per_m2": str(settings.primer_l_per_m2),
        "waterproofing_kg_per_m2": str(settings.waterproofing_kg_per_m2),
        "labor_kop_per_m2": {
            kind.value: {cls.value: price for cls, price in rates.items()}
            for kind, rates in settings.labor_kop_per_m2.items()
        },
        "materials": {
            kind.value: {
                "name": item.name,
                "pack_size": str(item.pack_size),
                "price_kop": item.price_kop,
                "pack_weight_kg": str(item.pack_weight_kg),
                "product_id": item.product_id,
            }
            for kind, item in settings.materials.items()
        },
    }


def result_to_dict(result: CalcResult) -> dict[str, Any]:
    return {
        "settings_version": result.settings_version,
        "surfaces": [
            {"kind": s.kind.value, "area_m2": str(s.area_m2),
             "area_with_waste_m2": str(s.area_with_waste_m2), "packs": s.packs}
            for s in result.surfaces
        ],
        "lines": [
            {"kind": line.kind, "name": line.name, "product_id": line.product_id,
             "quantity": str(line.quantity), "unit": line.unit,
             "quantity_base": str(line.quantity_base), "base_unit": line.base_unit,
             "total_kop": line.total_kop, "weight_kg": str(line.weight_kg),
             "surface_index": line.surface_index}
            for line in result.lines
        ],
        "total_kop": result.total_kop,
        "weight_kg": str(result.weight_kg),
        "warnings": [
            {"code": w.code, "message": w.message, "surface_index": w.surface_index}
            for w in result.warnings
        ],
    }
