import pytest

from apps.orders import services as order_services
from apps.orders.state import OrderStatus
from apps.payments import services
from apps.payments.models import Payment
from apps.payments.providers.fake import sign

pytestmark = pytest.mark.django_db


@pytest.fixture
def online_order(tile):
    order = order_services.create_order(
        customer=order_services.Customer(name="Іван", phone="+380671234567"),
        delivery_method="pickup", delivery={}, payment_method="online",
        lines=order_services.build_lines([order_services.LineRequest(tile.id, 3)]),
        delivery_kop=0,
    )
    services.start_payment(order)
    return order


def webhook(api, payment: Payment, status: str = "succeeded", amount: int | None = None,
            signature: str | None = None):
    body = {"reference": payment.reference, "status": status,
            "amount_kop": payment.amount_kop if amount is None else amount}
    return api.post("/api/v1/payments/webhook/fake",
                    {"payload": body, "signature": signature or sign(body)}, format="json")


def test_success_marks_order_paid(api, online_order):
    payment = online_order.payments.get()
    assert webhook(api, payment).status_code == 200
    online_order.refresh_from_db()
    assert online_order.payment_status == "paid"
    payment.refresh_from_db()
    assert payment.status == Payment.Status.SUCCEEDED


def test_replayed_webhook_is_ignored(api, online_order):
    payment = online_order.payments.get()
    webhook(api, payment)
    online_order.refresh_from_db()
    paid_at = online_order.paid_at
    assert webhook(api, payment).status_code == 200
    online_order.refresh_from_db()
    assert online_order.paid_at == paid_at


def test_bad_signature_rejected(api, online_order):
    payment = online_order.payments.get()
    response = webhook(api, payment, signature="forged")
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_signature"
    online_order.refresh_from_db()
    assert online_order.payment_status == "awaiting"


def test_amount_mismatch_needs_review(api, online_order):
    webhook(api, online_order.payments.get(), amount=100)
    online_order.refresh_from_db()
    assert online_order.needs_review is True
    assert online_order.payment_status == "awaiting"


def test_cancel_paid_order_requests_refund(api, online_order, run_on_commit):
    payment = online_order.payments.get()
    webhook(api, payment)
    with run_on_commit():
        order_services.transition(online_order.id, OrderStatus.CANCELLED)
    payment.refresh_from_db()
    assert payment.status == Payment.Status.REFUND_REQUESTED

    webhook(api, payment, status="refunded")
    online_order.refresh_from_db()
    assert online_order.payment_status == "refunded"


def test_retry_payment_endpoint(api, online_order):
    response = api.post(f"/api/v1/orders/{online_order.public_token}/pay")
    assert response.status_code == 200
    assert online_order.payments.count() == 2
