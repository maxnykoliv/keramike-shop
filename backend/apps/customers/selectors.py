from rest_framework.exceptions import NotAuthenticated

from apps.customers.models import Customer


def request_customer(request) -> Customer | None:
    user = getattr(request, "user", None)
    return user if isinstance(user, Customer) else None


def is_master(request) -> bool:
    customer = request_customer(request)
    return bool(customer and customer.is_master)


def require_customer(request) -> Customer:
    customer = request_customer(request)
    if customer is None:
        raise NotAuthenticated("Увійдіть, щоб продовжити")
    return customer

