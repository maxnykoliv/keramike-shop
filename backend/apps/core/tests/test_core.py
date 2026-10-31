from decimal import Decimal

import pytest

from apps.core import events
from apps.core.money import format_uah, round_kop, uah_to_kop


def test_money():
    assert round_kop(Decimal("100.5")) == 101
    assert uah_to_kop("650.00") == 65000
    assert format_uah(280800) == "2 808,00 грн"
    assert format_uah(5) == "0,05 грн"


def test_failing_handler_does_not_stop_others():
    calls = []

    def broken(payload):
        raise RuntimeError("boom")

    def working(payload):
        calls.append(payload)

    events.subscribe("test.event", broken)
    events.subscribe("test.event", working)
    events.dispatch("test.event", {"id": 1})
    assert calls == [{"id": 1}]


@pytest.mark.django_db
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "cache": "ok"}


@pytest.mark.django_db
def test_schema_generates(client):
    response = client.get("/api/v1/schema/")
    assert response.status_code == 200


def test_log_masking_keeps_timestamps():
    from apps.core.logging import mask_personal_data

    event = mask_personal_data(None, "info", {
        "event": "order from +380 67 123 45 67 and olena@example.com, id 2026-10-26",
        "timestamp": "2026-10-26T14:08:18.551123Z",
        "phone": "0671234567",
    })
    assert "123 45" not in event["event"]
    assert "olena@" not in event["event"]
    assert "2026-10-26" in event["event"]
    assert event["timestamp"] == "2026-10-26T14:08:18.551123Z"
    assert event["phone"] == "***"
