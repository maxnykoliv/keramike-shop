from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.customers.selectors import require_customer
from apps.orders import selectors
from apps.orders.api.serializers import PublicOrderSerializer
from apps.orders.models import Order


class AccountOrdersView(ListAPIView):
    """The customer's order history, including guest orders with the same phone number."""

    permission_classes = [IsAuthenticated]
    serializer_class = PublicOrderSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Order.objects.none()
        return selectors.customer_orders(require_customer(self.request).pk)
