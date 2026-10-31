"""Задачі розсилки. Безпечні для повтору: ключ дедуплікації не дає надіслати двічі."""

from celery import shared_task
from django.core.cache import cache

from apps.notifications import senders

SENT_TTL = 60 * 60 * 24 * 7


def _already_sent(key: str) -> bool:
    return cache.get(f"notif:{key}") is not None


def _mark_sent(key: str) -> None:
    cache.set(f"notif:{key}", 1, SENT_TTL)


@shared_task(bind=True, autoretry_for=(senders.SendError,), max_retries=5,
             retry_backoff=30, retry_backoff_max=1800)
def send_telegram(self, key: str, text: str) -> bool:
    if _already_sent(key):
        return False
    senders.send_telegram(text)
    _mark_sent(key)
    return True


@shared_task(bind=True, autoretry_for=(OSError,), max_retries=5, retry_backoff=30,
             retry_backoff_max=1800)
def send_email(self, key: str, to: str, subject: str, body: str) -> bool:
    if not to or _already_sent(key):
        return False
    senders.send_email(to, subject, body)
    _mark_sent(key)
    return True
