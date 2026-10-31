from django.conf import settings

from apps.payments.providers.base import PaymentLink, PaymentProvider, WebhookResult
from apps.payments.providers.fake import FakeProvider
from apps.payments.providers.liqpay import LiqPayProvider

PROVIDERS: dict[str, type] = {"fake": FakeProvider, "liqpay": LiqPayProvider}


def get_provider(name: str | None = None) -> PaymentProvider:
    name = name or settings.PAYMENT_PROVIDER
    try:
        return PROVIDERS[name]()
    except KeyError as exc:
        raise ValueError(f"Невідомий платіжний провайдер: {name}") from exc


__all__ = ["PaymentLink", "PaymentProvider", "WebhookResult", "get_provider"]
