import requests
from django.conf import settings
from django.core.mail import send_mail


class SendError(Exception):
    pass


def send_telegram(text: str) -> None:
    token, chat_id = settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML",
                  "disable_web_page_preview": True},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise SendError("Telegram недоступний") from exc
    if response.status_code != 200:
        raise SendError(f"Telegram відповів {response.status_code}")


def send_email(to: str, subject: str, body: str) -> None:
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
