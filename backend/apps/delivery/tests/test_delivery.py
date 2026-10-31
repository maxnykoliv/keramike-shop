import pytest
import responses
from django.conf import settings

from apps.cart import services as cart_services
from apps.delivery import services
from apps.delivery.models import DeliverySettings, Shipment
from apps.orders import services as order_services
from apps.orders.state import OrderStatus

pytestmark = pytest.mark.django_db
NP = settings.NOVA_POSHTA_API_URL


def test_city_search_is_cached(api, mocked_http):
    mocked_http.add(responses.POST, NP, json={"success": True, "data": [{"Addresses": [
        {"DeliveryCity": "city-ref", "Present": "м. Львів, Львівська обл."}]}]})
    first = api.get("/api/v1/delivery/np/cities?q=Львів").json()
    second = api.get("/api/v1/delivery/np/cities?q=львів").json()
    assert first == second == [{"ref": "city-ref", "name": "м. Львів, Львівська обл."}]
    assert len([c for c in mocked_http.calls if c.request.url == NP]) == 1


def test_np_error_is_503(api, mocked_http):
    mocked_http.add(responses.POST, NP, json={"success": False, "errors": ["API key expired"]})
    response = api.get("/api/v1/delivery/np/cities?q=Київ")
    assert response.status_code == 503


def test_quote_and_checkout_use_same_price(api, tile, mocked_http):
    DeliverySettings.objects.create(np_sender_city_ref="sender-city")
    mocked_http.add(responses.POST, NP, json={"success": True, "data": [{"Cost": 210}]})
    cart = cart_services.create_cart()
    cart_services.add_item(cart, tile.id, 3)

    quote = api.post("/api/v1/delivery/quote", {"method": "nova_poshta",
                                                "cart_token": cart.token,
                                                "city_ref": "city-ref"}, format="json").json()
    assert quote["cost_kop"] == 21000
    sent = mocked_http.calls[-1].request.body.decode()
    assert '"Weight": "96.000"' in sent

    order = api.post("/api/v1/orders/", {
        "cart_token": cart.token, "name": "Олена", "phone": "+380671234567",
        "delivery_method": "nova_poshta", "payment_method": "cod",
        "delivery": {"city_ref": "city-ref", "warehouse_ref": "wh-ref"},
        "quote_id": quote["quote_id"],
    }, format="json").json()
    assert order["delivery_kop"] == 21000
    assert order["total_kop"] == 280800 + 21000


def test_packed_np_order_gets_draft_shipment_and_completes_on_delivery(
        tile, mocked_http, run_on_commit):
    order = order_services.create_order(
        customer=order_services.Customer(name="Іван", phone="+380671234567"),
        delivery_method="nova_poshta", delivery={"city_ref": "c", "warehouse_ref": "w"},
        payment_method="cod",
        lines=order_services.build_lines([order_services.LineRequest(tile.id, 1)]),
    )
    with run_on_commit():
        order_services.transition(order.id, OrderStatus.CONFIRMED)
    with run_on_commit():
        order_services.transition(order.id, OrderStatus.PACKED)
    shipment = Shipment.objects.get(order=order)
    assert shipment.status == Shipment.Status.DRAFT

    order_services.transition(order.id, OrderStatus.SHIPPED)
    shipment.ttn = "20450000000000"
    shipment.status = Shipment.Status.CREATED
    shipment.save()
    mocked_http.add(responses.POST, NP, json={"success": True, "data": [
        {"Number": "20450000000000", "StatusCode": "9"}]})
    assert services.sync_parcel_statuses() == 1
    order.refresh_from_db()
    assert order.status == OrderStatus.COMPLETED


def test_create_ttn(tile, mocked_http):
    DeliverySettings.objects.create(np_sender_ref="s", np_sender_contact_ref="c",
                                    np_sender_city_ref="sc", np_sender_warehouse_ref="sw",
                                    np_sender_phone="380670000000")
    order = order_services.create_order(
        customer=order_services.Customer(name="Іван", phone="+380671234567"),
        delivery_method="nova_poshta", delivery={"city_ref": "c", "warehouse_ref": "w"},
        payment_method="cod",
        lines=order_services.build_lines([order_services.LineRequest(tile.id, 1)]),
    )
    shipment = Shipment.objects.create(order=order, carrier=Shipment.Carrier.NOVA_POSHTA)
    mocked_http.add(responses.POST, NP, json={"success": True, "data": [
        {"IntDocNumber": "20450000000001", "CostOnSite": 150}]})
    shipment = services.create_ttn(shipment.id)
    assert (shipment.ttn, shipment.cost_kop, shipment.status) == (
        "20450000000001", 15000, Shipment.Status.CREATED)
