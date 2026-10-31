"""Типи рушія калькулятора. Без Django: модуль має працювати як чистий Python."""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class Room(StrEnum):
    BATHROOM = "bathroom"
    TOILET = "toilet"
    KITCHEN = "kitchen"
    HALLWAY = "hallway"
    TERRACE = "terrace"
    LIVING = "living"
    OTHER = "other"


WET_ROOMS = frozenset({Room.BATHROOM, Room.TOILET})


class SurfaceKind(StrEnum):
    FLOOR = "floor"
    WALLS = "walls"


class Layout(StrEnum):
    STRAIGHT = "straight"
    OFFSET = "offset"
    DIAGONAL = "diagonal"
    HERRINGBONE = "herringbone"


class SizeClass(StrEnum):
    SMALL = "small"    # більша сторона до 300 мм
    MEDIUM = "medium"  # до 600 мм
    LARGE = "large"    # понад 600 мм


class Material(StrEnum):
    GLUE = "glue"
    GROUT = "grout"
    PRIMER = "primer"
    WATERPROOFING = "waterproofing"


@dataclass(frozen=True)
class Opening:
    width_m: Decimal
    height_m: Decimal
    count: int = 1


@dataclass(frozen=True)
class Tile:
    width_mm: int
    height_mm: int
    price_kop_per_m2: int
    thickness_mm: int = 8
    m2_per_pack: Decimal | None = None
    pcs_per_pack: int | None = None
    pack_weight_kg: Decimal | None = None
    product_id: int | None = None
    name: str = "Плитка"
    stock_m2: Decimal | None = None
    applications: tuple[str, ...] = ()


@dataclass(frozen=True)
class Surface:
    kind: SurfaceKind
    tile: Tile
    layout: Layout = Layout.STRAIGHT
    joint_mm: Decimal = Decimal("2")
    length_m: Decimal | None = None
    width_m: Decimal | None = None
    height_m: Decimal | None = None
    area_m2: Decimal | None = None
    openings: tuple[Opening, ...] = ()


@dataclass(frozen=True)
class Include:
    glue: bool = True
    grout: bool = True
    primer: bool = True
    waterproofing: bool = True
    labor: bool = True


@dataclass(frozen=True)
class CalcInput:
    room: Room
    surfaces: tuple[Surface, ...]
    include: Include = field(default_factory=Include)


@dataclass(frozen=True)
class MaterialProduct:
    name: str
    pack_size: Decimal
    price_kop: int
    pack_weight_kg: Decimal = Decimal("0")
    product_id: int | None = None


@dataclass(frozen=True)
class CalcSettings:
    version: int
    waste_by_layout: dict[Layout, Decimal]
    glue_kg_per_m2: dict[SizeClass, Decimal]
    grout_density: Decimal
    primer_l_per_m2: Decimal
    waterproofing_kg_per_m2: Decimal
    labor_kop_per_m2: dict[SurfaceKind, dict[SizeClass, int]]
    materials: dict[Material, MaterialProduct]


@dataclass(frozen=True)
class SurfaceResult:
    kind: SurfaceKind
    area_m2: Decimal
    area_with_waste_m2: Decimal
    packs: int


@dataclass(frozen=True)
class Line:
    kind: str
    name: str
    quantity: Decimal
    unit: str
    quantity_base: Decimal
    base_unit: str
    total_kop: int
    weight_kg: Decimal
    product_id: int | None = None
    surface_index: int | None = None


@dataclass(frozen=True)
class Warning:
    code: str
    message: str
    surface_index: int | None = None


@dataclass(frozen=True)
class CalcResult:
    settings_version: int
    surfaces: tuple[SurfaceResult, ...]
    lines: tuple[Line, ...]
    total_kop: int
    weight_kg: Decimal
    warnings: tuple[Warning, ...]
