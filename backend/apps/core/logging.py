"""Логи у JSON через structlog. Телефони й email маскуються."""

import re
from typing import Any

import structlog

# Українські номери: +380 67 123 45 67, 0671234567, (067) 123-45-67.
PHONE_RE = re.compile(
    r"(?<![\w:-])(?:\+?38)?\(?0[\s)]*\d{2}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?![\d:])"
)
EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+)")
SENSITIVE_KEYS = {"phone", "email", "customer_name", "password"}
SERVICE_KEYS = {"timestamp", "level", "logger", "request_id"}


def _mask(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    value = EMAIL_RE.sub(r"\1***\2", value)
    return PHONE_RE.sub(lambda m: m.group(0)[:4] + "***" + m.group(0)[-2:], value)


def mask_personal_data(_logger: Any, _name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    for key, value in list(event_dict.items()):
        if key in SERVICE_KEYS:
            continue
        if key in SENSITIVE_KEYS and value:
            event_dict[key] = "***"
        else:
            event_dict[key] = _mask(value)
    return event_dict


def configure_logging(*, json: bool, level: str = "INFO") -> dict[str, Any]:
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        mask_personal_data,
    ]
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    renderer = (
        structlog.processors.JSONRenderer() if json else structlog.dev.ConsoleRenderer()
    )
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structlog": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.processors.format_exc_info,
                    renderer,
                ],
                "foreign_pre_chain": shared,
            }
        },
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "structlog"}},
        "root": {"handlers": ["console"], "level": level},
        "loggers": {"django.db.backends": {"level": "WARNING"}},
    }
