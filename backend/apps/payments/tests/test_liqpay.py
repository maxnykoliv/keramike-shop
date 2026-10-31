import base64
import hashlib
import json

import pytest
from django.test import override_settings

from apps.core.exceptions import InvalidSignature
from apps.payments.providers.liqpay import LiqPayProvider


def signed(payload: dict, key: str = "private") -> dict:
    data = base64.b64encode(json.dumps(payload).encode()).decode()
    signature = base64.b64encode(hashlib.sha1(f"{key}{data}{key}".encode()).digest()).decode()
    return {"data": data, "signature": signature}


@override_settings(PAYMENT_PUBLIC_KEY="public", PAYMENT_PRIVATE_KEY="private")
def test_liqpay_webhook_and_link():
    provider = LiqPayProvider()
    result = provider.verify_webhook(signed({"order_id": "ref1", "status": "success",
                                             "amount": 2808.0, "payment_id": 42}))
    assert (result.reference, result.status, result.amount_kop) == ("ref1", "succeeded", 280800)

    link = provider.create_payment(reference="ref1", amount_kop=280800, description="Тест",
                                   result_url="https://site", server_url="https://api")
    params = dict(part.split("=", 1) for part in link.url.split("?", 1)[1].split("&"))
    decoded = json.loads(base64.b64decode(params["data"]))
    assert decoded["amount"] == "2808.00"
    assert decoded["order_id"] == "ref1"


@override_settings(PAYMENT_PUBLIC_KEY="public", PAYMENT_PRIVATE_KEY="private")
def test_liqpay_rejects_forged_signature():
    with pytest.raises(InvalidSignature):
        LiqPayProvider().verify_webhook(signed({"order_id": "x", "status": "success",
                                                "amount": 1}, key="attacker"))
