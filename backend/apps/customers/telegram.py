"""Клієнт Telegram Bot API для бота входу."""

from typing import Any

import requests
import structlog
from django.conf import settings

logger = structlog.get_logger(__name__)


def bot_url(start_token: str) -> str:
    return f"https://t.me/{settings.TELEGRAM_LOGIN_BOT_USERNAME}?start={start_token}"


def call(method: str, payload: dict[str, Any]) -> bool:
    token = settings.TELEGRAM_LOGIN_BOT_TOKEN
    if not token:
        logger.warning("telegram_login_bot_not_configured")
        return False
    try:
        response = requests.post(f"https://api.telegram.org/bot{token}/{method}",
                                 json=payload, timeout=10)
    except requests.RequestException:
        logger.warning("telegram_login_bot_unavailable", method=method)
        return False
    return response.status_code == 200


def send_message(chat_id: int, text: str, *, reply_markup: dict[str, Any] | None = None) -> bool:
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return call("sendMessage", payload)


CONTACT_KEYBOARD = {
    "keyboard": [[{"text": "Поділитися номером", "request_contact": True}]],
    "resize_keyboard": True,
    "one_time_keyboard": True,
}
REMOVE_KEYBOARD = {"remove_keyboard": True}
