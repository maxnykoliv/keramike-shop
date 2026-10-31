"""Реєструє вебхук бота входу: python manage.py telegram_set_webhook"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.customers import telegram


class Command(BaseCommand):
    help = "Реєструє вебхук Telegram-бота входу"

    def handle(self, *args, **options) -> None:
        if not (settings.TELEGRAM_LOGIN_BOT_TOKEN and settings.TELEGRAM_WEBHOOK_SECRET):
            raise CommandError("Задайте TELEGRAM_LOGIN_BOT_TOKEN і TELEGRAM_WEBHOOK_SECRET")
        url = f"{settings.API_URL}/api/v1/auth/telegram/webhook"
        ok = telegram.call("setWebhook", {
            "url": url,
            "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
            "allowed_updates": ["message"],
            "drop_pending_updates": True,
        })
        if not ok:
            raise CommandError("Telegram не прийняв вебхук")
        self.stdout.write(self.style.SUCCESS(f"Вебхук встановлено: {url}"))
