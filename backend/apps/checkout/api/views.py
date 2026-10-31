from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.checkout import services
from apps.checkout.api.serializers import CheckoutSerializer
from apps.core.security import client_ip, verify_turnstile
from apps.customers.selectors import request_customer
from apps.orders.services import Customer


class CheckoutView(APIView):
    throttle_scope = "forms"

    @extend_schema(
        request=CheckoutSerializer,
        parameters=[OpenApiParameter("Idempotency-Key", str, OpenApiParameter.HEADER)],
        responses={201: inline_serializer("CheckoutResult", {
            "number": serializers.CharField(),
            "public_token": serializers.CharField(),
            "total_kop": serializers.IntegerField(),
            "delivery_kop": serializers.IntegerField(allow_null=True),
            "payment_url": serializers.CharField(allow_null=True),
            "payment_retry": serializers.BooleanField(),
        })},
    )
    def post(self, request):
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        verify_turnstile(data.get("captcha"), client_ip(request))
        key = request.headers.get("Idempotency-Key") or None
        result = services.place_order(
            cart_token=data["cart_token"],
            customer=Customer(name=data["name"], phone=data["phone"], email=data["email"],
                              comment=data["comment"]),
            delivery_method=data["delivery_method"],
            delivery=dict(data.get("delivery") or {}),
            payment_method=data["payment_method"],
            quote_id=data.get("quote_id") or None,
            idempotency_key=key[:64] if key else None,
            account=request_customer(request),
        )
        order = result.order
        return Response({
            "number": order.number,
            "public_token": order.public_token,
            "total_kop": order.total_kop,
            "delivery_kop": order.delivery_kop,
            "payment_url": result.payment_url,
            "payment_retry": result.payment_retry,
        }, status=status.HTTP_201_CREATED)


class RetryPaymentView(APIView):
    throttle_scope = "forms"

    @extend_schema(request=None, responses=inline_serializer(
        "PaymentLink", {"payment_url": serializers.CharField()}))
    def post(self, request, token: str):
        return Response({"payment_url": services.retry_payment(token)})
