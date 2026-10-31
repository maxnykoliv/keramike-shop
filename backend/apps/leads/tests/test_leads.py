import json

import pytest

from apps.calc import services as calc_services
from apps.leads import services
from apps.leads.models import Lead
from conftest import TELEGRAM_URL

pytestmark = pytest.mark.django_db


@pytest.fixture
def estimate(published_settings, tile):
    return calc_services.save_estimate({
        "room": "bathroom",
        "surfaces": [{"kind": "floor", "product_id": tile.id, "length_m": "2.0",
                      "width_m": "1.7"}],
        "include": {"glue": True, "grout": True, "primer": False, "waterproofing": False,
                    "labor": True},
    })


def test_create_lead_notifies_manager(api, estimate, run_on_commit, mocked_http):
    with run_on_commit():
        response = api.post("/api/v1/leads/", {
            "name": "Петро", "phone": "+380501112233", "estimate_code": estimate.public_code,
        }, format="json")
    assert response.status_code == 201
    lead = Lead.objects.get()
    assert lead.estimate == estimate
    texts = [json.loads(c.request.body)["text"] for c in mocked_http.calls
             if c.request.url == TELEGRAM_URL]
    assert any("Петро" in text for text in texts)


def test_invalid_phone(api, db):
    response = api.post("/api/v1/leads/", {"name": "Петро", "phone": "abc"}, format="json")
    assert response.status_code == 400


def test_convert_to_order(estimate):
    lead = services.create_lead(name="Петро", phone="+380501112233", estimate=estimate)
    order = services.convert_to_order(lead.id)
    lead.refresh_from_db()
    assert lead.status == Lead.Status.CONVERTED
    assert lead.order == order
    assert order.items.count() == 3  # tile, glue, grout; labour is not a product
    assert order.subtotal_kop == 343800
