"""Domain event bus.

Lower layers publish events and higher layers subscribe in AppConfig.ready. An event is
queued only after the transaction commits, so a rollback sends nothing.
"""

from collections import defaultdict
from collections.abc import Callable
from typing import Any

import structlog
from django.db import transaction

logger = structlog.get_logger(__name__)

Handler = Callable[[dict[str, Any]], None]
_handlers: dict[str, list[Handler]] = defaultdict(list)


def subscribe(event: str, handler: Handler) -> None:
    if handler not in _handlers[event]:
        _handlers[event].append(handler)


def publish(event: str, payload: dict[str, Any]) -> None:
    from apps.core.tasks import dispatch_event

    transaction.on_commit(lambda: dispatch_event.delay(event, payload))


def dispatch(event: str, payload: dict[str, Any]) -> None:
    """Calls every subscriber. One failing does not stop the others."""
    for handler in list(_handlers.get(event, [])):
        try:
            handler(payload)
        except Exception:
            logger.exception("event_handler_failed", event_name=event,
                             handler=handler.__qualname__)
