"""One-time code channels. Add Viber or SMS with a new class and an entry in CHANNELS."""

from django.conf import settings

from apps.core.exceptions import DomainError
from apps.customers.channels.base import CodeChannel
from apps.customers.channels.console import ConsoleChannel

CHANNELS: dict[str, type] = {
    "console": ConsoleChannel,
    # "viber": ViberChannel,  # via a provider (TurboSMS etc.) with SMS fallback
    # "sms": SmsChannel,
}


def enabled_channels() -> list[str]:
    return [name for name in settings.AUTH_CODE_CHANNELS if name in CHANNELS]


def get_channel(name: str) -> CodeChannel:
    if name not in enabled_channels():
        raise DomainError("Цей спосіб входу поки недоступний", field="channel",
                          code="channel_unavailable")
    return CHANNELS[name]()


__all__ = ["CodeChannel", "enabled_channels", "get_channel"]
