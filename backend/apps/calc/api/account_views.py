from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from apps.calc import selectors
from apps.calc.api.serializers import AccountEstimateSerializer
from apps.calc.models import Estimate
from apps.customers.selectors import require_customer


class AccountEstimatesView(ListAPIView):
    """Estimates saved by a logged-in customer."""

    permission_classes = [IsAuthenticated]
    serializer_class = AccountEstimateSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Estimate.objects.none()
        return selectors.customer_estimates(require_customer(self.request).pk)
