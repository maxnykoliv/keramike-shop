from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.delivery import services
from apps.orders.state import DeliveryMethod


class CitiesView(APIView):
    @extend_schema(parameters=[OpenApiParameter("q", str)], responses=inline_serializer(
        "City", {"ref": serializers.CharField(), "name": serializers.CharField()}, many=True))
    def get(self, request):
        query = request.GET.get("q", "").strip()
        if len(query) < 2:
            return Response([])
        return Response(services.search_cities(query))


class WarehousesView(APIView):
    @extend_schema(
        parameters=[OpenApiParameter("city", str), OpenApiParameter("q", str)],
        responses=inline_serializer("Warehouse", {
            "ref": serializers.CharField(), "name": serializers.CharField(),
            "number": serializers.CharField(), "type": serializers.CharField(),
        }, many=True),
    )
    def get(self, request):
        city = request.GET.get("city", "")
        if not city:
            return Response([])
        return Response(services.warehouses(city, request.GET.get("q", "")))


class QuoteSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=DeliveryMethod.choices)
    cart_token = serializers.CharField(max_length=64)
    city_ref = serializers.CharField(max_length=64, required=False, default="")


class QuoteView(APIView):
    @extend_schema(request=QuoteSerializer, responses=OpenApiTypes.OBJECT,
                   description="cost_kop = null означає, що вартість уточнить менеджер")
    def post(self, request):
        serializer = QuoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(services.quote(**serializer.validated_data))
