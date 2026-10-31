"""Провайдер для розробки й тестів: підпис HMAC-SHA256 ключем PAYMENT_PRIVATE_KEY."""

import hashlib
import hmac
import json
from typing import Any

from django.conf import settings

from apps.core.exceptions import InvalidSignature
from apps.payments.providers.base import PaymentLink, WebhookResult


def sign(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(settings.PAYMENT_PRIVATE_KEY.encode(), body, hashlib.sha256).hexdigest()


class FakeProvider:
    name = "fake"

    def create_payment(self, *, reference: str, amount_kop: int, description: str,
                       result_url: str, server_url: str) -> PaymentLink:
        return PaymentLink(url=f"{result_url}?fake_payment={reference}",
                           provider_payment_id=f"fake-{reference}")

    def verify_webhook(self, data: dict[str, Any]) -> WebhookResult:
        payload = data.get("payload")
        signature = data.get("signature", "")
        if not isinstance(payload, dict) or not hmac.compare_digest(sign(payload), signature):
            raise InvalidSignature()
        return WebhookResult(
            reference=payload["reference"],
            status=payload["status"],
            amount_kop=int(payload["amount_kop"]),
            provider_payment_id=payload.get("provider_payment_id", ""),
            raw=payload,
        )

    def refund(self, *, reference: str, amount_kop: int) -> None:
        return None
