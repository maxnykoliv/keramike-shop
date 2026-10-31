from django.apps import AppConfig


class OrdersConfig(AppConfig):
    name = "apps.orders"
    verbose_name = "Замовлення"

    def ready(self) -> None:
        from apps.core.events import subscribe
        from apps.customers.events import CUSTOMER_LOGGED_IN
        from apps.orders.services import claim_guest_orders

        subscribe(CUSTOMER_LOGGED_IN, claim_guest_orders)
