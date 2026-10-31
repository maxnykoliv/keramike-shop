"""Доменні винятки і єдиний формат помилок API: {code, message, field}."""

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class DomainError(Exception):
    code = "domain_error"
    message = "Операцію не можна виконати"
    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None, *, field: str | None = None,
                 code: str | None = None, extra: dict[str, Any] | None = None) -> None:
        self.message = message or self.message
        self.field = field
        if code:
            self.code = code
        self.extra = extra or {}
        super().__init__(self.message)


class NotFound(DomainError):
    code = "not_found"
    message = "Не знайдено"
    status_code = status.HTTP_404_NOT_FOUND


class OutOfStock(DomainError):
    code = "out_of_stock"
    message = "Недостатньо товару на складі"
    status_code = status.HTTP_409_CONFLICT


class InvalidTransition(DomainError):
    code = "invalid_transition"
    message = "Такий перехід статусу заборонений"
    status_code = status.HTTP_409_CONFLICT


class PaymentRequired(DomainError):
    code = "payment_required"
    message = "Онлайн-замовлення можна відправити лише після оплати"
    status_code = status.HTTP_409_CONFLICT


class PaymentMismatch(DomainError):
    code = "payment_mismatch"
    message = "Сума оплати не збігається із сумою замовлення"


class InvalidSignature(DomainError):
    code = "invalid_signature"
    message = "Невалідний підпис"


class ProviderUnavailable(DomainError):
    code = "provider_unavailable"
    message = "Зовнішній сервіс тимчасово недоступний"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class EmptyCart(DomainError):
    code = "empty_cart"
    message = "Кошик порожній"


class SpamSuspected(DomainError):
    code = "captcha_failed"
    message = "Не вдалося підтвердити, що ви не робот"
    status_code = status.HTTP_403_FORBIDDEN


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DomainError):
        body: dict[str, Any] = {"code": exc.code, "message": exc.message, "field": exc.field}
        body.update(exc.extra)
        return Response(body, status=exc.status_code)

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    if isinstance(exc, ValidationError):
        response.data = {
            "code": "validation_error",
            "message": "Перевірте введені дані",
            "field": None,
            "errors": response.data,
        }
    elif isinstance(exc, APIException):
        response.data = {
            "code": exc.get_codes() if isinstance(exc.get_codes(), str) else "error",
            "message": str(exc.detail),
            "field": None,
        }
    return response
