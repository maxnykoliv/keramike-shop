from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    name = "apps.payments"
    verbose_name = "Оплати"

    def ready(self) -> None:
        from apps.core.events import subscribe
        from apps.orders.events import ORDER_CANCELLED
        from apps.payments.services import refund_cancelled_order

        subscribe(ORDER_CANCELLED, refund_cancelled_order)
