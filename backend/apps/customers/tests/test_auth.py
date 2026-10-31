import json
from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.phone import InvalidPhone, normalize_phone
from apps.customers.channels.console import outbox
from apps.customers.models import Customer, CustomerSession, TelegramLogin
from conftest import LOGIN_BOT_URL

pytestmark = pytest.mark.django_db
HOOK = {"HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN": "hook-secret"}


@pytest.mark.parametrize("raw", ["+380 (67) 123-45-67", "0671234567", "380671234567",
                                 "671234567"])
def test_normalize_phone(raw):
    assert normalize_phone(raw) == "+380671234567"


def test_normalize_phone_rejects_garbage():
    with pytest.raises(InvalidPhone):
        normalize_phone("12345")


def tg_message(user_id: int, *, text: str | None = None, contact: dict | None = None) -> dict:
    message = {"message_id": 1, "chat": {"id": user_id, "type": "private"},
               "from": {"id": user_id, "first_name": "Олена", "username": "olena"}}
    if text is not None:
        message["text"] = text
    if contact is not None:
        message["contact"] = contact
    return {"update_id": 1, "message": message}


def bot_messages(mocked_http) -> list[dict]:
    return [json.loads(c.request.body) for c in mocked_http.calls
            if c.request.url == LOGIN_BOT_URL]


def start(api) -> tuple[dict, str]:
    data = api.post("/api/v1/auth/telegram/start").json()
    start_token = data["bot_url"].split("start=")[1]
    assert data["bot_url"].startswith("https://t.me/keramike_login_bot?start=")
    return data, start_token


def poll(api, data) -> dict:
    return api.post("/api/v1/auth/telegram/poll", {"login_id": data["login_id"],
                                                   "poll_secret": data["poll_secret"]},
                    format="json").json()


def test_telegram_login_new_customer(api, mocked_http, run_on_commit):
    data, token = start(api)
    assert poll(api, data)["status"] == "pending"

    with run_on_commit():
        api.post("/api/v1/auth/telegram/webhook", tg_message(42, text=f"/start {token}"),
                 format="json", **HOOK)
    assert poll(api, data)["status"] == "awaiting_contact"
    assert bot_messages(mocked_http)[-1]["reply_markup"]["keyboard"][0][0]["request_contact"]

    with run_on_commit():
        api.post("/api/v1/auth/telegram/webhook",
                 tg_message(42, contact={"user_id": 42, "phone_number": "380671234567"}),
                 format="json", **HOOK)
    result = poll(api, data)
    assert result["status"] == "confirmed"
    assert result["customer"]["phone"] == "+380671234567"
    customer = Customer.objects.get(phone="+380671234567")
    assert (customer.telegram_user_id, customer.name) == (42, "Олена")

    second = api.post("/api/v1/auth/telegram/poll", {"login_id": data["login_id"],
                                                     "poll_secret": data["poll_secret"]},
                      format="json")
    assert second.status_code == 404


def test_known_telegram_user_confirms_without_contact(api, run_on_commit):
    Customer.objects.create(phone="+380501112233", telegram_user_id=7)
    data, token = start(api)
    with run_on_commit():
        api.post("/api/v1/auth/telegram/webhook", tg_message(7, text=f"/start {token}"),
                 format="json", **HOOK)
    result = poll(api, data)
    assert result["status"] == "confirmed"
    assert result["customer"]["phone"] == "+380501112233"


def test_foreign_contact_is_rejected(api, run_on_commit):
    data, token = start(api)
    with run_on_commit():
        api.post("/api/v1/auth/telegram/webhook", tg_message(42, text=f"/start {token}"),
                 format="json", **HOOK)
        api.post("/api/v1/auth/telegram/webhook",
                 tg_message(42, contact={"user_id": 99, "phone_number": "380671234567"}),
                 format="json", **HOOK)
    assert poll(api, data)["status"] == "awaiting_contact"


def test_wrong_poll_secret(api):
    data, _ = start(api)
    response = api.post("/api/v1/auth/telegram/poll",
                        {"login_id": data["login_id"], "poll_secret": "guess"}, format="json")
    assert response.status_code == 404


def test_webhook_requires_secret(api):
    response = api.post("/api/v1/auth/telegram/webhook", tg_message(1, text="/start x"),
                        format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="wrong")
    assert response.status_code == 403


def test_expired_login(api):
    data, _ = start(api)
    TelegramLogin.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
    assert poll(api, data)["status"] == "expired"


def test_session_me_and_logout(customer_api, api):
    client, customer = customer_api()
    me = client.get("/api/v1/account/me").json()
    assert me["phone"] == customer.phone

    updated = client.patch("/api/v1/account/me", {"name": "Іван", "is_master": True},
                           format="json").json()
    assert (updated["name"], updated["is_master"]) == ("Іван", False)

    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/account/me").status_code == 401
    assert api.get("/api/v1/account/me").status_code in (401, 403)


def test_invalid_token_is_401(api):
    api.credentials(HTTP_AUTHORIZATION="Bearer nope")
    response = api.get("/api/v1/catalog/categories")
    assert response.status_code == 401


def test_expired_session(customer_api):
    client, customer = customer_api()
    CustomerSession.objects.filter(customer=customer).update(
        expires_at=timezone.now() - timedelta(seconds=1))
    assert client.get("/api/v1/account/me").status_code == 401


def test_addresses(customer_api):
    client, _ = customer_api()
    first = client.post("/api/v1/account/addresses", {
        "delivery_method": "nova_poshta", "city_ref": "c", "city_name": "Львів",
        "warehouse_ref": "w", "warehouse_name": "Відділення 1"}, format="json")
    assert first.status_code == 201
    assert first.json()["is_default"] is True

    second = client.post("/api/v1/account/addresses", {
        "delivery_method": "local", "address": "вул. Шевченка, 1", "is_default": True},
        format="json").json()
    addresses = client.get("/api/v1/account/addresses").json()
    assert [a["id"] for a in addresses if a["is_default"]] == [second["id"]]

    bad = client.post("/api/v1/account/addresses", {"delivery_method": "nova_poshta"},
                      format="json")
    assert bad.status_code == 400
    assert client.delete(f"/api/v1/account/addresses/{second['id']}").status_code == 204


def test_other_customers_address_is_hidden(customer_api):
    owner, _ = customer_api("+380671111111")
    other, _ = customer_api("+380672222222")
    created = owner.post("/api/v1/account/addresses", {
        "delivery_method": "local", "address": "вул. Лесі, 5"}, format="json").json()
    assert other.get(f"/api/v1/account/addresses/{created['id']}").status_code == 404


def test_code_login(api):
    outbox.clear()
    methods = api.get("/api/v1/auth/methods").json()
    assert methods == {"telegram": True, "code_channels": ["console"]}

    sent = api.post("/api/v1/auth/code/request",
                    {"phone": "067 123 45 67", "channel": "console"}, format="json")
    assert sent.status_code == 202
    phone, code = outbox[-1]
    assert phone == "+380671234567"

    again = api.post("/api/v1/auth/code/request",
                     {"phone": "0671234567", "channel": "console"}, format="json")
    assert again.json()["code"] == "code_too_soon"

    wrong = "000000" if code != "000000" else "111111"
    bad = api.post("/api/v1/auth/code/verify", {"phone": "0671234567", "code": wrong},
                   format="json")
    assert bad.json()["code"] == "code_invalid"

    ok = api.post("/api/v1/auth/code/verify", {"phone": "0671234567", "code": code},
                  format="json")
    assert ok.status_code == 200
    assert ok.json()["customer"]["phone"] == "+380671234567"

    reused = api.post("/api/v1/auth/code/verify", {"phone": "0671234567", "code": code},
                      format="json")
    assert reused.status_code == 400


def test_unknown_channel(api):
    response = api.post("/api/v1/auth/code/request",
                        {"phone": "0671234567", "channel": "viber"}, format="json")
    assert response.json()["code"] == "channel_unavailable"
