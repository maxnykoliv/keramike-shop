"""LiqPay API v3: data = base64(json), signature = base64(sha1(private + data + private))."""

import base64
import hashlib
import json
from decimal import Decimal
from typing import Any

import requests
from django.conf import settings

from apps.core.exceptions import InvalidSignature, ProviderUnavailable
from apps.core.money import kop_to_uah, uah_to_kop
from apps.payments.providers.base import PaymentLink, WebhookResult

CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout"
REQUEST_URL = "https://www.liqpay.ua/api/request"

STATUS_MAP = {
    "success": "succeeded",
    "sandbox": "succeeded",
    "failure": "failed",
    "error": "failed",
    "reversed": "refunded",
}


class LiqPayProvider:
    name = "liqpay"

    def __init__(self) -> None:
        self.public_key = settings.PAYMENT_PUBLIC_KEY
        self.private_key = settings.PAYMENT_PRIVATE_KEY

    def _encode(self, params: dict[str, Any]) -> tuple[str, str]:
        data = base64.b64encode(json.dumps(params).encode()).decode()
        return data, self._signature(data)

    def _signature(self, data: str) -> str:
        raw = f"{self.private_key}{data}{self.private_key}".encode()
        return base64.b64encode(hashlib.sha1(raw).digest()).decode()

    def create_payment(self, *, reference: str, amount_kop: int, description: str,
                       result_url: str, server_url: str) -> PaymentLink:
        data, signature = self._encode({
            "version": 3,
            "public_key": self.public_key,
            "action": "pay",
            "amount": str(kop_to_uah(amount_kop)),
            "currency": "UAH",
            "description": description,
            "order_id": reference,
            "result_url": result_url,
            "server_url": server_url,
        })
        return PaymentLink(url=f"{CHECKOUT_URL}?data={data}&signature={signature}")

    def verify_webhook(self, data: dict[str, Any]) -> WebhookResult:
        encoded = data.get("data", "")
        if not encoded or self._signature(encoded) != data.get("signature"):
            raise InvalidSignature()
        payload = json.loads(base64.b64decode(encoded))
        return WebhookResult(
            reference=payload["order_id"],
            status=STATUS_MAP.get(payload.get("status", ""), "pending"),
            amount_kop=uah_to_kop(Decimal(str(payload["amount"]))),
            provider_payment_id=str(payload.get("payment_id", "")),
            raw=payload,
        )

    def refund(self, *, reference: str, amount_kop: int) -> None:
        data, signature = self._encode({
            "version": 3,
            "public_key": self.public_key,
            "action": "refund",
            "order_id": reference,
            "amount": str(kop_to_uah(amount_kop)),
        })
        try:
            response = requests.post(REQUEST_URL, data={"data": data, "signature": signature},
                                     timeout=15)
            result = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ProviderUnavailable() from exc
        if result.get("status") not in {"reversed", "success"}:
            reason = result.get("err_description")
            raise ProviderUnavailable(f"LiqPay відхилив повернення: {reason}")
