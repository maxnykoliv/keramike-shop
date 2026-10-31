from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "apps.notifications"
    verbose_name = "Сповіщення"

    def ready(self) -> None:
        from apps.notifications.handlers import register

        register()
