from django.apps import AppConfig


class CustomersConfig(AppConfig):
    name = "apps.customers"
    verbose_name = "Клієнти"

    def ready(self) -> None:
        from apps.customers import schema  # noqa: F401  — Bearer scheme for OpenAPI
