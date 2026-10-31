"""Cloudflare Turnstile checks on public forms and client IP detection."""

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
        return  # disabled in development and tests
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
        return  # a Cloudflare outage must not block sales
    if not ok:
        raise SpamSuspected()


def _valid_ip(value: str) -> str | None:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        return None


def client_ip(request) -> str | None:
    """Client IP for rate limits, admin login lockouts and the session log.

    The site calls the API on behalf of the browser and passes the client IP in X-Client-IP
    together with a shared secret. Without the secret the header is ignored. A client can
    prepend anything to X-Forwarded-For, so we take the address added by our own proxy
    (Railway): the TRUSTED_PROXY_COUNT-th entry from the end.
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
