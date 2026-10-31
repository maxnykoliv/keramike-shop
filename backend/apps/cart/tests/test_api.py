import pytest

from apps.calc import services as calc_services
from apps.cart.models import Cart
from conftest import ProductFactory

pytestmark = pytest.mark.django_db


def test_cart_flow(api, tile):
    token = api.post("/api/v1/carts/").json()["token"]
    added = api.post(f"/api/v1/carts/{token}/items", {"product_id": tile.id, "qty": 2},
                     format="json")
    assert added.status_code == 201
    api.post(f"/api/v1/carts/{token}/items", {"product_id": tile.id, "qty": 1}, format="json")

    cart = api.get(f"/api/v1/carts/{token}").json()
    assert len(cart["lines"]) == 1
    line = cart["lines"][0]
    assert (line["qty"], line["base_qty"], line["total_kop"]) == (3, "4.320", 280800)
    assert cart["weight_kg"] == "96.000"

    updated = api.patch(f"/api/v1/carts/{token}/items/{line['id']}", {"qty": 5},
                        format="json").json()
    assert updated["lines"][0]["qty"] == 5

    emptied = api.delete(f"/api/v1/carts/{token}/items/{line['id']}").json()
    assert emptied["lines"] == []


def test_hidden_product_cannot_be_added(api):
    product = ProductFactory.create(status="hidden")
    token = api.post("/api/v1/carts/").json()["token"]
    response = api.post(f"/api/v1/carts/{token}/items", {"product_id": product.id, "qty": 1},
                        format="json")
    assert response.status_code == 404


def test_add_from_estimate_skips_labor(api, published_settings, tile):
    estimate = calc_services.save_estimate({
        "room": "bathroom",
        "surfaces": [{"kind": "floor", "product_id": tile.id, "length_m": "2.0",
                      "width_m": "1.7"}],
        "include": {"glue": True, "grout": True, "primer": False, "waterproofing": False,
                    "labor": True},
    })
    token = api.post("/api/v1/carts/").json()["token"]
    cart = api.post(f"/api/v1/carts/{token}/from-estimate/{estimate.public_code}").json()
    assert [line["qty"] for line in cart["lines"]] == [3, 1, 1]
    assert {line["group_label"] for line in cart["lines"]} == {
        f"Кошторис {estimate.public_code}"
    }
    assert cart["subtotal_kop"] == 343800


def test_closed_cart_is_not_found(api):
    cart = Cart.objects.create()
    cart.closed_at = cart.created_at
    cart.save()
    assert api.get(f"/api/v1/carts/{cart.token}").status_code == 404
