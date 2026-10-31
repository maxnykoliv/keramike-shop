from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders import selectors
from apps.orders.api.serializers import PublicOrderSerializer


class OrderStatusView(APIView):
    @extend_schema(responses=PublicOrderSerializer)
    def get(self, request, token: str):
        return Response(PublicOrderSerializer(selectors.get_by_token(token)).data)
