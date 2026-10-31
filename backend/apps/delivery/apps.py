from django.apps import AppConfig


class DeliveryConfig(AppConfig):
    name = "apps.delivery"
    verbose_name = "Доставка"

    def ready(self) -> None:
        from apps.core.events import subscribe
        from apps.delivery.services import on_order_status_changed
        from apps.orders.events import ORDER_STATUS_CHANGED

        subscribe(ORDER_STATUS_CHANGED, on_order_status_changed)
