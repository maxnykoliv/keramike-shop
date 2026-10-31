"""Stats on the admin home page. Owner only."""

from datetime import timedelta
from typing import Any

from django.db.models import Count, Sum
from django.utils import timezone

from apps.calc.models import Estimate
from apps.core.money import format_uah
from apps.core.roles import is_owner
from apps.leads.models import Lead
from apps.orders.models import Order
from apps.orders.state import OrderStatus, PaymentStatus


def _period_stats(since) -> dict[str, Any]:
    orders = Order.objects.filter(created_at__gte=since).exclude(status=OrderStatus.CANCELLED)
    revenue = orders.filter(payment_status=PaymentStatus.PAID).aggregate(s=Sum("total_kop"))["s"]
    return {
        "orders": orders.count(),
        "revenue": format_uah(revenue or 0),
        "leads": Lead.objects.filter(created_at__gte=since).count(),
        "estimates": Estimate.objects.filter(created_at__gte=since).count(),
    }


def dashboard_callback(request, context: dict[str, Any]) -> dict[str, Any]:
    if not is_owner(request.user):
        return context
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    context["shop_stats"] = [
        {"title": "Сьогодні", **_period_stats(today)},
        {"title": "7 днів", **_period_stats(now - timedelta(days=7))},
        {"title": "30 днів", **_period_stats(now - timedelta(days=30))},
    ]
    context["open_orders"] = list(
        Order.objects.exclude(status__in=[OrderStatus.COMPLETED, OrderStatus.CANCELLED])
        .values("status").annotate(count=Count("id")).order_by("status")
    )
    context["needs_review"] = Order.objects.filter(needs_review=True).count()
    return context
