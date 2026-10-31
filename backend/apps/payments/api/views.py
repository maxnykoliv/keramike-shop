import json

import structlog
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.parsers import FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import InvalidSignature
from apps.payments import services

logger = structlog.get_logger(__name__)


class WebhookView(APIView):
    parser_classes = [JSONParser, FormParser]

    @extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT,
                   description="Викликає платіжний сервіс, не фронтенд")
    def post(self, request, provider: str):
        data = request.data.dict() if hasattr(request.data, "dict") else dict(request.data)
        try:
            services.handle_webhook(provider, data)
        except InvalidSignature:
            logger.warning("payment_webhook_bad_signature", provider=provider,
                           body=json.dumps(data)[:500])
            raise
        return Response({"status": "ok"})
