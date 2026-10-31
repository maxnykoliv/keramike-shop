"""Перевірка Cloudflare Turnstile на публічних формах і визначення IP клієнта."""

import hmac
import ipaddress

import requests
import structlog
from django.conf import settings

from apps.core.exceptions import SpamSuspected

logger = structlog.get_logger(__name__)
VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(token: str | None, remote_ip: str | None) -> None:
    secret = settings.TURNSTILE_SECRET_KEY
    if not secret:
        return  # вимкнено в розробці й тестах
    if not token:
        raise SpamSuspected()
    try:
        response = requests.post(
            VERIFY_URL,
            data={"secret": secret, "response": token, "remoteip": remote_ip or ""},
            timeout=5,
        )
        ok = response.json().get("success", False)
    except (requests.RequestException, ValueError):
        logger.warning("turnstile_unavailable")
        return  # недоступність Cloudflare не має блокувати продажі
    if not ok:
        raise SpamSuspected()


def _valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def client_ip(request) -> str | None:
    """IP клієнта для лімітів, блокування входу в адмінку й журналу сесій.

    Сайт звертається до API від імені браузера й передає IP клієнта в X-Client-IP разом зі
    спільним секретом. Без секрету цьому заголовку не віримо. У X-Forwarded-For клієнт може
    дописати що завгодно зліва, тож беремо адресу, яку додав наш власний проксі (Railway):
    TRUSTED_PROXY_COUNT-ту з кінця.
    """
    secret = settings.BFF_SHARED_SECRET
    if secret and hmac.compare_digest(request.headers.get("X-BFF-Secret", ""), secret):
        ip = _valid_ip(request.headers.get("X-Client-IP", ""))
        if ip:
            return ip
    proxies = settings.TRUSTED_PROXY_COUNT
    chain = [part for part in request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")
             if part.strip()]
    if proxies and len(chain) >= proxies:
        ip = _valid_ip(chain[-proxies])
        if ip:
            return ip
    return request.META.get("REMOTE_ADDR")
