import hmac

from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.security import client_ip
from apps.customers import services, telegram
from apps.customers.api.serializers import (
    AddressSerializer,
    CodeRequestSerializer,
    CodeVerifySerializer,
    CustomerSerializer,
    LoginResultSerializer,
    TelegramPollResultSerializer,
    TelegramPollSerializer,
    TelegramStartSerializer,
)
from apps.customers.channels import enabled_channels
from apps.customers.models import CustomerAddress
from apps.customers.selectors import require_customer


def _login_payload(result: services.LoginResult) -> dict:
    return {"token": result.token, "expires_at": result.session.expires_at,
            "customer": CustomerSerializer(result.customer).data}


def _client(request) -> dict:
    return {"user_agent": request.headers.get("User-Agent", ""), "ip": client_ip(request)}


class AuthMethodsView(APIView):
    @extend_schema(responses=inline_serializer("AuthMethods", {
        "telegram": serializers.BooleanField(),
        "code_channels": serializers.ListField(child=serializers.CharField()),
    }))
    def get(self, request):
        return Response({"telegram": bool(settings.TELEGRAM_LOGIN_BOT_USERNAME),
                         "code_channels": enabled_channels()})


class TelegramStartView(APIView):
    throttle_scope = "auth"

    @extend_schema(request=None, responses={201: TelegramStartSerializer})
    def post(self, request):
        attempt, poll_secret = services.start_telegram_login()
        return Response({"login_id": attempt.pk, "poll_secret": poll_secret,
                         "bot_url": telegram.bot_url(attempt.start_token),
                         "expires_at": attempt.expires_at}, status=status.HTTP_201_CREATED)


class TelegramPollView(APIView):
    @extend_schema(request=TelegramPollSerializer, responses=TelegramPollResultSerializer,
                   description="Сайт опитує кожні 2 секунди, поки статус не confirmed або expired")
    def post(self, request):
        serializer = TelegramPollSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        state, result = services.poll_telegram_login(
            str(serializer.validated_data["login_id"]),
            serializer.validated_data["poll_secret"], **_client(request))
        if result is None:
            return Response({"status": state})
        return Response({"status": state, **_login_payload(result)})


class TelegramWebhookView(APIView):
    """Updates from Telegram. Checks the secret header and always responds with 200."""

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT,
                   description="Викликає Telegram, не фронтенд")
    def post(self, request):
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        expected = settings.TELEGRAM_WEBHOOK_SECRET
        if not expected or not hmac.compare_digest(secret, expected):
            return Response(status=status.HTTP_403_FORBIDDEN)
        services.handle_telegram_update(request.data)
        return Response({"ok": True})


class CodeRequestView(APIView):
    throttle_scope = "auth"

    @extend_schema(request=CodeRequestSerializer, responses={202: OpenApiTypes.OBJECT})
    def post(self, request):
        serializer = CodeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        record = services.request_code(serializer.validated_data["phone"],
                                       serializer.validated_data["channel"])
        return Response({"expires_at": record.expires_at}, status=status.HTTP_202_ACCEPTED)


class CodeVerifyView(APIView):
    throttle_scope = "auth"

    @extend_schema(request=CodeVerifySerializer, responses=LoginResultSerializer)
    def post(self, request):
        serializer = CodeVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.verify_code(serializer.validated_data["phone"],
                                      serializer.validated_data["code"], **_client(request))
        return Response(_login_payload(result))


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        services.logout(request.auth)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        services.logout_all(require_customer(request))
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CustomerSerializer
    http_method_names = ["get", "patch"]

    def get_object(self):
        return require_customer(self.request)


class AddressListView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    pagination_class = None

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomerAddress.objects.none()
        return require_customer(self.request).addresses.all()

    def perform_create(self, serializer):
        customer = require_customer(self.request)
        address = serializer.save(customer=customer)
        if address.is_default or customer.addresses.count() == 1:
            services.set_default_address(address)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AddressSerializer
    http_method_names = ["get", "patch", "delete"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return CustomerAddress.objects.none()
        return require_customer(self.request).addresses.all()

    def perform_update(self, serializer):
        address = serializer.save()
        if address.is_default:
            services.set_default_address(address)

