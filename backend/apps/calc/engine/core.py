"""The calculator engine: the source of truth for every amount.

Rules that must match the TypeScript port (checked by calc-cases):
- area is rounded to 0.01 m² with ROUND_HALF_UP;
- packs, bags and buckets always round up to a whole number;
- tile total = packs × m² per pack × price per m², rounded to the kopiyka once.
"""

from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal

from apps.calc.engine.errors import CalcValidationError
from apps.calc.engine.types import (
    WET_ROOMS,
    CalcInput,
    CalcResult,
    CalcSettings,
    Line,
    Material,
    MaterialProduct,
    SizeClass,
    Surface,
    SurfaceKind,
    SurfaceResult,
    Tile,
    Warning,
)

CENT = Decimal("0.01")
MILLI = Decimal("0.001")
MIN_SIDE = Decimal("0.1")
MAX_SIDE = Decimal("50")
MAX_HEIGHT = Decimal("5")
MAX_AREA = Decimal("1000")


def round2(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def ceil_int(value: Decimal) -> int:
    return int(value.to_integral_value(rounding=ROUND_CEILING))


def kop(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def size_class(tile: Tile) -> SizeClass:
    side = max(tile.width_mm, tile.height_mm)
    if side <= 300:
        return SizeClass.SMALL
    if side <= 600:
        return SizeClass.MEDIUM
    return SizeClass.LARGE


def m2_per_pack(tile: Tile, path: str) -> Decimal:
    if tile.m2_per_pack:
        return tile.m2_per_pack
    if tile.pcs_per_pack:
        area = Decimal(tile.width_mm) * Decimal(tile.height_mm) / Decimal(1_000_000)
        return (area * tile.pcs_per_pack).quantize(MILLI, rounding=ROUND_HALF_UP)
    raise CalcValidationError("pack_unknown", "Невідомо, скільки м² в упаковці", f"{path}.tile")


def _check_side(value: Decimal | None, path: str, *, maximum: Decimal = MAX_SIDE) -> Decimal:
    if value is None:
        raise CalcValidationError("required", "Вкажіть розмір", path)
    if value < MIN_SIDE or value > maximum:
        raise CalcValidationError(
            "out_of_range", f"Розмір має бути від {MIN_SIDE} до {maximum} м", path
        )
    return value


def surface_area(surface: Surface, path: str) -> Decimal:
    if surface.area_m2 is not None:
        if surface.area_m2 <= 0 or surface.area_m2 > MAX_AREA:
            raise CalcValidationError("out_of_range", "Площа має бути від 0 до 1000 м²",
                                      f"{path}.area_m2")
        return round2(surface.area_m2)

    length = _check_side(surface.length_m, f"{path}.length_m")
    width = _check_side(surface.width_m, f"{path}.width_m")
    if surface.kind == SurfaceKind.FLOOR:
        return round2(length * width)

    height = _check_side(surface.height_m, f"{path}.height_m", maximum=MAX_HEIGHT)
    gross = 2 * (length + width) * height
    openings = sum((o.width_m * o.height_m * o.count for o in surface.openings), Decimal("0"))
    if openings >= gross:
        raise CalcValidationError("openings_exceed_area",
                                  "Прорізи не можуть бути більшими за площу стін",
                                  f"{path}.openings")
    return round2(gross - openings)


def grout_kg_per_m2(tile: Tile, joint_mm: Decimal, density: Decimal) -> Decimal:
    a = Decimal(tile.width_mm)
    b = Decimal(tile.height_mm)
    return (a + b) / (a * b) * Decimal(tile.thickness_mm) * joint_mm * density


def _material_line(kind: Material, product: MaterialProduct, amount: Decimal,
                   base_unit: str) -> Line:
    packs = ceil_int(amount / product.pack_size)
    return Line(
        kind=kind.value,
        name=product.name,
        quantity=Decimal(packs),
        unit="pack",
        quantity_base=round2(amount),
        base_unit=base_unit,
        total_kop=packs * product.price_kop,
        weight_kg=(product.pack_weight_kg * packs).quantize(MILLI),
        product_id=product.product_id,
    )


def calculate(data: CalcInput, settings: CalcSettings) -> CalcResult:
    if not data.surfaces:
        raise CalcValidationError("required", "Додайте хоча б одну поверхню", "surfaces")

    surfaces: list[SurfaceResult] = []
    lines: list[Line] = []
    warnings: list[Warning] = []
    glue_kg = Decimal("0")
    grout_kg = Decimal("0")
    total_area = Decimal("0")
    labor_kop = Decimal("0")

    for index, surface in enumerate(data.surfaces):
        path = f"surfaces[{index}]"
        tile = surface.tile
        area = surface_area(surface, path)
        waste = settings.waste_by_layout[surface.layout]
        area_with_waste = area * (1 + waste)
        per_pack = m2_per_pack(tile, path)
        packs = ceil_int(area_with_waste / per_pack)
        bought_m2 = per_pack * packs
        cls = size_class(tile)

        surfaces.append(SurfaceResult(kind=surface.kind, area_m2=area,
                                      area_with_waste_m2=round2(area_with_waste), packs=packs))
        lines.append(Line(
            kind="tile",
            name=tile.name,
            quantity=Decimal(packs),
            unit="pack",
            quantity_base=round2(bought_m2),
            base_unit="m2",
            total_kop=kop(bought_m2 * tile.price_kop_per_m2),
            weight_kg=((tile.pack_weight_kg or Decimal("0")) * packs).quantize(MILLI),
            product_id=tile.product_id,
            surface_index=index,
        ))

        if tile.stock_m2 is not None and bought_m2 > tile.stock_m2:
            message = f"На складі {tile.stock_m2} м², потрібно {round2(bought_m2)} м²"
            warnings.append(Warning("insufficient_stock", message, index))
        if (surface.kind == SurfaceKind.FLOOR and tile.applications
                and "floor" not in tile.applications):
            warnings.append(Warning("tile_not_for_floor",
                                    "Ця плитка не призначена для підлоги", index))

        glue_kg += area * settings.glue_kg_per_m2[cls]
        grout_kg += area * grout_kg_per_m2(tile, surface.joint_mm, settings.grout_density)
        labor_kop += area * settings.labor_kop_per_m2[surface.kind][cls]
        total_area += area

    include = data.include
    wanted = [
        (include.glue, Material.GLUE, glue_kg, "kg"),
        (include.grout, Material.GROUT, grout_kg, "kg"),
        (include.primer, Material.PRIMER, total_area * settings.primer_l_per_m2, "l"),
        (include.waterproofing and data.room in WET_ROOMS, Material.WATERPROOFING,
         total_area * settings.waterproofing_kg_per_m2, "kg"),
    ]
    for enabled, material, amount, base_unit in wanted:
        if not enabled:
            continue
        product = settings.materials.get(material)
        if product is None:
            warnings.append(Warning("material_not_configured",
                                    f"Матеріал «{material.value}» не налаштований"))
            continue
        lines.append(_material_line(material, product, amount, base_unit))

    if data.room in WET_ROOMS and not include.waterproofing:
        warnings.append(Warning("waterproofing_recommended",
                                "Для ванної й туалету рекомендуємо гідроізоляцію"))

    if include.labor:
        lines.append(Line(kind="labor", name="Робота майстра", quantity=round2(total_area),
                          unit="m2", quantity_base=round2(total_area), base_unit="m2",
                          total_kop=kop(labor_kop), weight_kg=Decimal("0.000")))

    return CalcResult(
        settings_version=settings.version,
        surfaces=tuple(surfaces),
        lines=tuple(lines),
        total_kop=sum(line.total_kop for line in lines),
        weight_kg=sum((line.weight_kg for line in lines), Decimal("0")).quantize(MILLI),
        warnings=tuple(warnings),
    )
