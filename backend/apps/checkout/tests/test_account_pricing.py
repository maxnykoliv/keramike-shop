"""Accounts and master prices in the catalog, cart, calculator and orders."""

import pytest

from apps.cart import services as cart_services
from apps.customers import services as customer_services
from apps.customers.models import Customer
from apps.orders.models import Order

pytestmark = pytest.mark.django_db
MASTER_PRICE = 55000  # instead of 65 000 kop/m²


@pytest.fixture
def master_tile(tile):
    tile.master_price_kop = MASTER_PRICE
    tile.save()
    return tile


def floor(product_id: int) -> dict:
    return {"room": "bathroom",
            "surfaces": [{"kind": "floor", "product_id": product_id, "length_m": "2.0",
                          "width_m": "1.7"}],
            "include": {"glue": False, "grout": False, "primer": False,
                        "waterproofing": False, "labor": False}}


def test_personal_prices(api, customer_api, master_tile):
    retail = api.post("/api/v1/catalog/prices", {"ids": [master_tile.id]}, format="json").json()
    assert retail == {"is_master": False, "prices": {str(master_tile.id): 65000}}

    master, _ = customer_api(master=True)
    personal = master.post("/api/v1/catalog/prices", {"ids": [master_tile.id]},
                           format="json").json()
    assert personal == {"is_master": True, "prices": {str(master_tile.id): MASTER_PRICE}}

    public = api.get(f"/api/v1/catalog/products/{master_tile.slug}").json()
    assert public["price_kop"] == 65000
    assert "master_price_kop" not in public


def test_master_cart_and_checkout(customer_api, master_tile):
    client, customer = customer_api(master=True)
    cart = cart_services.create_cart()
    cart_services.add_item(cart, master_tile.id, 3)

    view = client.get(f"/api/v1/carts/{cart.token}").json()
    assert view["subtotal_kop"] == 3 * 144 * 550

    order = client.post("/api/v1/orders/", {
        "cart_token": cart.token, "name": "Майстер", "phone": customer.phone,
        "delivery_method": "pickup", "payment_method": "cod"}, format="json").json()
    saved = Order.objects.get(number=order["number"])
    assert saved.total_kop == 3 * 144 * 550
    assert saved.customer == customer


def test_regular_customer_pays_retail(customer_api, master_tile):
    client, _ = customer_api(master=False)
    cart = cart_services.create_cart()
    cart_services.add_item(cart, master_tile.id, 3)
    assert client.get(f"/api/v1/carts/{cart.token}").json()["subtotal_kop"] == 280800


def test_master_calculator_and_saved_estimates(customer_api, published_settings, master_tile):
    client, _ = customer_api(master=True)
    result = client.post("/api/v1/calc/estimate", floor(master_tile.id), format="json").json()
    assert result["lines"][0]["total_kop"] == 3 * 144 * 550

    saved = client.post("/api/v1/calc/estimates", {**floor(master_tile.id),
                                                   "title": "Ванна на дачі"},
                        format="json").json()
    listed = client.get("/api/v1/account/estimates").json()["results"]
    assert [(e["code"], e["title"], e["room"]) for e in listed] == [
        (saved["code"], "Ванна на дачі", "bathroom")]


def test_guest_orders_appear_after_login(api, tile, run_on_commit):
    cart = cart_services.create_cart()
    cart_services.add_item(cart, tile.id, 1)
    guest = api.post("/api/v1/orders/", {
        "cart_token": cart.token, "name": "Гість", "phone": "+380 67 555 44 33",
        "delivery_method": "pickup", "payment_method": "cod"}, format="json").json()
    assert Order.objects.get(number=guest["number"]).phone == "+380675554433"

    customer = Customer.objects.create(phone="+380675554433")
    with run_on_commit():
        token = customer_services.login(customer).token
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    orders = api.get("/api/v1/account/orders").json()["results"]
    assert [o["number"] for o in orders] == [guest["number"]]
    assert orders[0]["items"][0]["product_id"] == tile.id


def test_account_requires_login(api):
    for url in ["/api/v1/account/orders", "/api/v1/account/estimates",
                "/api/v1/account/addresses"]:
        assert api.get(url).status_code in (401, 403)
