"""Registers the login bot webhook: python manage.py telegram_set_webhook"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.customers import telegram


class Command(BaseCommand):
    help = "Registers the Telegram login bot webhook"

    def handle(self, *args, **options) -> None:
        if not (settings.TELEGRAM_LOGIN_BOT_TOKEN and settings.TELEGRAM_WEBHOOK_SECRET):
            raise CommandError("Set TELEGRAM_LOGIN_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET")
        url = f"{settings.API_URL}/api/v1/auth/telegram/webhook"
        ok = telegram.call("setWebhook", {
            "url": url,
            "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
            "allowed_updates": ["message"],
            "drop_pending_updates": True,
        })
        if not ok:
            raise CommandError("Telegram rejected the webhook")
        self.stdout.write(self.style.SUCCESS(f"Webhook set: {url}"))
