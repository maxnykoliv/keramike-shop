"""Читання каталогу.

Ціноутворення рядка тут, щоб кошик, замовлення й калькулятор рахували однаково.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.contrib.postgres.search import TrigramSimilarity
from django.core.cache import cache
from django.db.models import Count, Max, Min, Q, QuerySet

from apps.catalog.models import Category, Product, TileSpec
from apps.core.exceptions import NotFound
from apps.core.money import round_kop

CACHE_VERSION_KEY = "catalog:version"
QTY = Decimal("0.001")


def catalog_cache_version() -> int:
    version = cache.get(CACHE_VERSION_KEY)
    if version is None:
        cache.add(CACHE_VERSION_KEY, 1, timeout=None)
        version = cache.get(CACHE_VERSION_KEY, 1)
    return int(version)


def public_products() -> QuerySet[Product]:
    return (
        Product.objects.filter(status=Product.Status.ACTIVE, category__is_active=True)
        .select_related("category", "collection__manufacturer", "tile_spec", "material_spec")
        .prefetch_related("images")
    )


def get_public_product(slug: str) -> Product:
    product = (
        public_products()
        .prefetch_related("relations__related__images", "relations__related__tile_spec")
        .filter(slug=slug)
        .first()
    )
    if product is None:
        raise NotFound("Товар не знайдено")
    return product


def products_by_ids(ids: list[int], *, active_only: bool = True) -> dict[int, Product]:
    qs = Product.objects.select_related("tile_spec", "material_spec").filter(id__in=ids)
    if active_only:
        qs = qs.filter(status=Product.Status.ACTIVE)
    return {product.id: product for product in qs}


def category_tree() -> list[dict[str, Any]]:
    categories = list(Category.objects.filter(is_active=True).order_by("sort", "name"))
    by_parent: dict[int | None, list[Category]] = {}
    for category in categories:
        by_parent.setdefault(category.parent_id, []).append(category)

    def build(parent_id: int | None) -> list[dict[str, Any]]:
        return [
            {"slug": c.slug, "name": c.name, "children": build(c.id)}
            for c in by_parent.get(parent_id, [])
        ]

    return build(None)


def search_products(query: str, limit: int = 10) -> QuerySet[Product]:
    query = query.strip()
    return (
        public_products()
        .annotate(similarity=TrigramSimilarity("name", query))
        .filter(Q(similarity__gt=0.2) | Q(name__icontains=query) | Q(sku__icontains=query))
        .order_by("-similarity", "name")[:limit]
    )


def facets(qs: QuerySet[Product]) -> dict[str, Any]:
    """Доступні значення фільтрів і кількість товарів для кожного."""
    ids = qs.values("id")
    tiles = TileSpec.objects.filter(product_id__in=ids)
    prices = qs.aggregate(min=Min("price_kop"), max=Max("price_kop"))
    return {
        "kinds": list(qs.values("kind").annotate(count=Count("id")).order_by("kind")),
        "sizes": [
            {"size": f"{row['width_mm']}x{row['height_mm']}", "count": row["count"]}
            for row in tiles.values("width_mm", "height_mm")
            .annotate(count=Count("product_id"))
            .order_by("width_mm", "height_mm")
        ],
        "colors": list(
            tiles.exclude(color="").values("color").annotate(count=Count("product_id"))
            .order_by("color")
        ),
        "surfaces": list(
            tiles.exclude(surface="").values("surface").annotate(count=Count("product_id"))
            .order_by("surface")
        ),
        "manufacturers": [
            {"slug": row["collection__manufacturer__slug"],
             "name": row["collection__manufacturer__name"], "count": row["count"]}
            for row in qs.exclude(collection__isnull=True)
            .values("collection__manufacturer__slug", "collection__manufacturer__name")
            .annotate(count=Count("id"))
            .order_by("collection__manufacturer__name")
        ],
        "price_kop": {"min": prices["min"], "max": prices["max"]},
    }


@dataclass(frozen=True)
class LinePrice:
    """Рядок кошика або замовлення. Для плитки qty — упаковки, base_qty — м²."""

    product_id: int
    sku: str
    name: str
    unit: str
    qty: int
    base_qty: Decimal
    price_kop: int
    total_kop: int
    weight_kg: Decimal
    stock_units: Decimal
    available: bool


def effective_price(product: Product, *, master: bool = False) -> int:
    if master and product.master_price_kop is not None:
        return product.master_price_kop
    return product.price_kop


def personal_prices(ids: list[int], *, master: bool) -> dict[int, int]:
    products = Product.objects.filter(id__in=ids, status=Product.Status.ACTIVE).only(
        "id", "price_kop", "master_price_kop")
    return {p.id: effective_price(p, master=master) for p in products}


def line_price(product: Product, qty: int, *, master: bool = False) -> LinePrice:
    spec = getattr(product, "tile_spec", None)
    if spec is not None:
        base_qty = (Decimal(qty) * spec.effective_m2_per_pack).quantize(QTY)
        weight = Decimal(qty) * (spec.pack_weight_kg or Decimal("0"))
        unit = "pack"
    else:
        base_qty = Decimal(qty)
        weight = Decimal(qty) * (product.weight_kg or Decimal("0"))
        unit = product.unit
    price_kop = effective_price(product, master=master)
    total = round_kop(base_qty * Decimal(price_kop))
    on_order = product.stock_status == Product.StockStatus.ON_ORDER
    return LinePrice(
        product_id=product.id,
        sku=product.sku,
        name=product.name,
        unit=unit,
        qty=qty,
        base_qty=base_qty,
        price_kop=price_kop,
        total_kop=total,
        weight_kg=weight.quantize(QTY),
        stock_units=base_qty,
        available=on_order or product.available_qty >= base_qty,
    )
