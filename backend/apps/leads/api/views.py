from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.calc.selectors import get_estimate
from apps.core.security import client_ip, verify_turnstile
from apps.customers.api.serializers import PhoneField
from apps.leads import services


class LeadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    phone = PhoneField(max_length=32)
    comment = serializers.CharField(max_length=2000, required=False, default="",
                                    allow_blank=True)
    estimate_code = serializers.CharField(max_length=8, required=False)
    captcha = serializers.CharField(required=False, allow_blank=True)


class LeadCreateView(APIView):
    throttle_scope = "forms"

    @extend_schema(request=LeadSerializer, responses={201: inline_serializer(
        "LeadCreated", {"id": serializers.IntegerField(), "status": serializers.CharField()})})
    def post(self, request):
        serializer = LeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        verify_turnstile(data.get("captcha"), client_ip(request))
        estimate = get_estimate(data["estimate_code"]) if data.get("estimate_code") else None
        lead = services.create_lead(name=data["name"], phone=data["phone"],
                                    comment=data["comment"], estimate=estimate)
        return Response({"id": lead.pk, "status": lead.status}, status=status.HTTP_201_CREATED)
