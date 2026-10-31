from decimal import Decimal

import pytest

from apps.catalog import services
from apps.catalog.models import Product
from apps.catalog.selectors import line_price
from apps.core.exceptions import OutOfStock
from conftest import CategoryFactory, ProductFactory, make_tile

pytestmark = pytest.mark.django_db


def test_list_and_filters(api):
    floor = make_tile(width=600, height=600, applications=["floor"])
    wall = make_tile(width=300, height=600, applications=["wall"])
    ProductFactory.create(status=Product.Status.HIDDEN)

    data = api.get("/api/v1/catalog/products").json()
    assert data["count"] == 2

    by_size = api.get("/api/v1/catalog/products?size=600x300").json()
    assert [p["id"] for p in by_size["results"]] == [wall.id]

    by_application = api.get("/api/v1/catalog/products?application=floor").json()
    assert [p["id"] for p in by_application["results"]] == [floor.id]

    ordered = api.get("/api/v1/catalog/products?ordering=-price").json()
    assert ordered["results"][0]["price_display"].endswith("грн")


def test_category_filter_includes_children(api):
    parent = CategoryFactory.create(slug="plytka")
    child = CategoryFactory.create(slug="vanna", parent=parent)
    product = make_tile(category=child)
    data = api.get("/api/v1/catalog/products?category=plytka").json()
    assert [p["id"] for p in data["results"]] == [product.id]
    tree = api.get("/api/v1/catalog/categories").json()
    assert tree[0]["children"][0]["slug"] == "vanna"


def test_facets(api):
    make_tile(width=600, height=600)
    make_tile(width=600, height=600)
    make_tile(width=300, height=600)
    data = api.get("/api/v1/catalog/facets").json()
    sizes = {row["size"]: row["count"] for row in data["sizes"]}
    assert sizes == {"300x600": 1, "600x600": 2}
    assert data["price_kop"]["min"] == 65000


def test_detail_and_404(api, tile):
    data = api.get(f"/api/v1/catalog/products/{tile.slug}").json()
    assert data["tile_spec"]["m2_per_pack"] == "1.440"
    assert api.get("/api/v1/catalog/products/missing").status_code == 404


def test_search(api):
    make_tile(name="Marble Grey Lux")
    make_tile(name="Wood Oak")
    results = api.get("/api/v1/catalog/search?q=marble").json()
    assert [p["name"] for p in results] == ["Marble Grey Lux"]


def test_cache_invalidated_on_save(api, tile, django_capture_on_commit_callbacks):
    first = api.get(f"/api/v1/catalog/products/{tile.slug}").json()
    assert first["price_kop"] == 65000
    with django_capture_on_commit_callbacks(execute=True):
        tile.price_kop = 70000
        tile.save()
    second = api.get(f"/api/v1/catalog/products/{tile.slug}").json()
    assert second["price_kop"] == 70000


def test_line_price_for_tile_and_material(tile):
    price = line_price(tile, 3)
    assert price.base_qty == Decimal("4.320")
    assert price.total_kop == 280800
    assert price.weight_kg == Decimal("96.000")

    glue = ProductFactory.create(price_kop=45000, weight_kg=Decimal("25"))
    price = line_price(glue, 2)
    assert price.total_kop == 90000
    assert price.weight_kg == Decimal("50.000")


def test_reserve_release_write_off(tile):
    assert services.reserve(tile.id, Decimal("40")) == Decimal("40")
    tile.refresh_from_db()
    assert tile.available_qty == Decimal("60")
    with pytest.raises(OutOfStock):
        services.reserve(tile.id, Decimal("61"))
    services.release(tile.id, Decimal("10"))
    services.write_off(tile.id, Decimal("30"))
    tile.refresh_from_db()
    assert (tile.stock_qty, tile.reserved_qty) == (Decimal("70"), Decimal("0"))


def test_on_order_product_is_not_reserved(tile):
    tile.stock_status = Product.StockStatus.ON_ORDER
    tile.stock_qty = Decimal("0")
    tile.save()
    assert services.reserve(tile.id, Decimal("10")) == Decimal("0")


def test_filter_by_ids(api):
    first = make_tile(name="Перша")
    make_tile(name="Друга")
    third = make_tile(name="Третя")
    data = api.get(f"/api/v1/catalog/products?ids={first.id},{third.id}").json()
    assert sorted(p["id"] for p in data["results"]) == sorted([first.id, third.id])
