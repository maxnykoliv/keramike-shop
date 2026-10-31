from decimal import Decimal

import pytest
from django.core import mail

from apps.cart import services as cart_services
from apps.orders.models import Order
from apps.payments.models import Payment
from conftest import TELEGRAM_URL

pytestmark = pytest.mark.django_db


def make_cart(product, qty=3) -> str:
    cart = cart_services.create_cart()
    cart_services.add_item(cart, product.id, qty)
    return cart.token


def payload(token: str, **overrides) -> dict:
    return {
        "cart_token": token, "name": "Олена", "phone": "+380 67 123 45 67",
        "email": "olena@example.com", "delivery_method": "pickup", "payment_method": "cod",
        **overrides,
    }


def test_cod_pickup_order(api, tile, run_on_commit, mocked_http):
    token = make_cart(tile)
    with run_on_commit():
        response = api.post("/api/v1/orders/", payload(token), format="json")
    assert response.status_code == 201, response.json()
    data = response.json()
    assert data["number"].startswith("KER-")
    assert data["total_kop"] == 280800
    assert data["delivery_kop"] == 0
    assert data["payment_url"] is None

    order = Order.objects.get(number=data["number"])
    assert order.payment_status == "on_delivery"
    assert order.items.get().qty_base == Decimal("4.320")
    assert api.get(f"/api/v1/carts/{token}").status_code == 404

    telegram = [c for c in mocked_http.calls if c.request.url == TELEGRAM_URL]
    assert len(telegram) == 1
    assert data["number"] in telegram[0].request.body.decode()
    assert mail.outbox[0].subject == f"Замовлення {data['number']} прийнято"


def test_online_order_gets_payment_link(api, tile):
    token = make_cart(tile)
    response = api.post("/api/v1/orders/", payload(token, payment_method="online"),
                        format="json")
    data = response.json()
    payment = Payment.objects.get(order__number=data["number"])
    assert payment.status == Payment.Status.PENDING
    assert data["payment_url"].endswith(f"fake_payment={payment.reference}")


def test_idempotency_key_returns_same_order(api, tile):
    token = make_cart(tile)
    headers = {"HTTP_IDEMPOTENCY_KEY": "key-123"}
    first = api.post("/api/v1/orders/", payload(token), format="json", **headers).json()
    second = api.post("/api/v1/orders/", payload(token), format="json", **headers).json()
    assert first["number"] == second["number"]
    assert Order.objects.count() == 1


def test_out_of_stock_blocks_order(api, tile):
    token = make_cart(tile, qty=100)  # 144 m² with 100 in stock
    response = api.post("/api/v1/orders/", payload(token), format="json")
    assert response.status_code == 409
    assert response.json()["code"] == "out_of_stock"
    assert Order.objects.count() == 0


def test_nova_poshta_requires_warehouse(api, tile):
    token = make_cart(tile)
    response = api.post("/api/v1/orders/", payload(token, delivery_method="nova_poshta"),
                        format="json")
    assert response.status_code == 400


def test_unknown_quote_means_delivery_to_be_confirmed(api, tile):
    token = make_cart(tile)
    response = api.post("/api/v1/orders/", payload(
        token, delivery_method="local", delivery={"address": "вул. Шевченка, 1"},
        quote_id="missing"), format="json")
    assert response.json()["delivery_kop"] is None


def test_order_status_page(api, tile):
    token = make_cart(tile)
    created = api.post("/api/v1/orders/", payload(token), format="json").json()
    status = api.get(f"/api/v1/orders/{created['public_token']}").json()
    assert status["status"] == "new"
    assert status["items"][0]["qty"] == 3
