from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calc import selectors, services
from apps.calc.api.serializers import (
    CalcInputSerializer,
    CalcResultSerializer,
    EstimateCreatedSerializer,
    EstimateCreateSerializer,
    EstimateDetailSerializer,
    PdfStatusSerializer,
)
from apps.calc.tasks import render_estimate_pdf
from apps.customers.selectors import is_master, request_customer


class ConfigView(APIView):
    """Активні налаштування у форматі рушія — для миттєвого розрахунку в браузері."""

    @extend_schema(responses=OpenApiTypes.OBJECT,
                   description="Формат як у calc-cases/settings.json")
    def get(self, request):
        return Response(selectors.settings_dict(selectors.active_settings(),
                                                master=is_master(request)))


class EstimateView(APIView):
    throttle_scope = "estimates"

    @extend_schema(request=CalcInputSerializer, responses=CalcResultSerializer)
    def post(self, request):
        serializer = CalcInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        calculation = services.calculate(serializer.validated_data,
                                         master=is_master(request))
        return Response(calculation.result_dict)


class EstimateCreateView(APIView):
    throttle_scope = "estimates"

    @extend_schema(request=EstimateCreateSerializer, responses={201: EstimateCreatedSerializer})
    def post(self, request):
        serializer = EstimateCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        source = data.pop("source")
        title = data.pop("title", "")
        estimate = services.save_estimate(data, source=source,
                                          customer=request_customer(request), title=title)
        return Response({"code": estimate.public_code, "result": estimate.result},
                        status=status.HTTP_201_CREATED)


class EstimateDetailView(APIView):
    @extend_schema(responses=EstimateDetailSerializer)
    def get(self, request, code: str):
        estimate = selectors.get_estimate(code)
        current = services.recalculate(estimate)
        return Response({
            "code": estimate.public_code,
            "created_at": estimate.created_at,
            "input": estimate.input,
            "result": estimate.result,
            "current": current,
            "changed": current is None or current["total_kop"] != estimate.total_kop,
        })


class EstimatePdfView(APIView):
    @extend_schema(responses={200: PdfStatusSerializer, 202: PdfStatusSerializer})
    def get(self, request, code: str):
        estimate = selectors.get_estimate(code)
        if not estimate.pdf:
            render_estimate_pdf.delay(estimate.id)
            estimate.refresh_from_db()
        if estimate.pdf:
            return Response({"status": "ready", "url": estimate.pdf.url})
        return Response({"status": "rendering"}, status=status.HTTP_202_ACCEPTED)
