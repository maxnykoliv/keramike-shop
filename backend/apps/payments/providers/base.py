"""Payment provider interface. A new bank means a new class; orders stay unchanged."""

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class PaymentLink:
    url: str
    provider_payment_id: str = ""


@dataclass(frozen=True)
class WebhookResult:
    reference: str
    status: str  # pending | succeeded | failed | refunded
    amount_kop: int
    provider_payment_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict)


class PaymentProvider(Protocol):
    name: str

    def create_payment(self, *, reference: str, amount_kop: int, description: str,
                       result_url: str, server_url: str) -> PaymentLink: ...

    def verify_webhook(self, data: dict[str, Any]) -> WebhookResult: ...

    def refund(self, *, reference: str, amount_kop: int) -> None: ...
