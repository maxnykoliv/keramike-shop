"""Development and test channel: the code goes to the log, to the outbox and, optionally, to a file.

The frontend e2e tests read that file (AUTH_CONSOLE_OUTBOX_FILE) to log in with a code.
"""

import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)
outbox: list[tuple[str, str]] = []


class ConsoleChannel:
    name = "console"

    def send_code(self, phone: str, code: str) -> None:
        outbox.append((phone, code))
        logger.info("login_code", channel=self.name, code=code)
        path = getattr(settings, "AUTH_CONSOLE_OUTBOX_FILE", "")
        if path:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(f"{phone} {code}\n")
