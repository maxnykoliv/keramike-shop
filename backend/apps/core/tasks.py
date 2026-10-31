import gzip
import subprocess
from datetime import UTC, datetime
from typing import Any

import structlog
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.core import events

logger = structlog.get_logger(__name__)


@shared_task
def dispatch_event(event: str, payload: dict[str, Any]) -> None:
    events.dispatch(event, payload)


@shared_task(autoretry_for=(subprocess.CalledProcessError,), max_retries=2,
             default_retry_delay=600)
def backup_database() -> str | None:
    """Нічний pg_dump у файлове сховище (R2). Вмикається змінною BACKUP_ENABLED."""
    if not settings.BACKUP_ENABLED:
        return None
    db = settings.DATABASES["default"]
    env = {"PGPASSWORD": str(db.get("PASSWORD") or "")}
    cmd = [
        "pg_dump", "--no-owner", "--format=plain",
        "-h", str(db.get("HOST") or "localhost"),
        "-p", str(db.get("PORT") or 5432),
        "-U", str(db.get("USER") or ""),
        str(db["NAME"]),
    ]
    dump = subprocess.run(cmd, check=True, capture_output=True, env=env).stdout
    name = f"backups/{datetime.now(UTC):%Y-%m-%d_%H%M}.sql.gz"
    saved = default_storage.save(name, ContentFile(gzip.compress(dump)))
    logger.info("backup_saved", path=saved, size=len(dump))
    return saved
