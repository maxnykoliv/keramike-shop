"""Підписники на доменні події. Читають актуальний стан і ставлять розсилку в чергу."""

from typing import Any

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import escape

from apps.core.events import subscribe
from apps.core.money import format_uah
from apps.leads import selectors as lead_selectors
from apps.leads.services import LEAD_CREATED
from apps.notifications import tasks
from apps.orders import events as order_events
from apps.orders import selectors as order_selectors
from apps.orders.models import Order


def _admin_link(path: str) -> str:
    return f"{settings.API_URL}/admin/{path}"


def _order_summary(order: Order) -> str:
    delivery = "уточнюється" if order.delivery_kop is None else format_uah(order.delivery_kop)
    return (f"<b>{order.number}</b> на {format_uah(order.total_kop)}\n"
            f"{escape(order.customer_name)}, {escape(order.phone)}\n"
            f"{order.get_delivery_method_display()}, доставка: {delivery}\n"
            f"Оплата: {order.get_payment_method_display()}\n"
            f"{_admin_link(f'orders/order/{order.pk}/change/')}")


def on_order_created(payload: dict[str, Any]) -> None:
    order = order_selectors.get_order(payload["order_id"])
    tasks.send_telegram.delay(f"order-created-{order.pk}",
                              f"Нове замовлення\n{_order_summary(order)}")
    if order.email:
        body = render_to_string("notifications/order_created.txt", {
            "order": order, "items": order.items.all(),
            "total": format_uah(order.total_kop),
            "status_url": f"{settings.SITE_URL}/orders/{order.public_token}",
        })
        tasks.send_email.delay(f"order-created-email-{order.pk}", order.email,
                               f"Замовлення {order.number} прийнято", body)


def on_status_changed(payload: dict[str, Any]) -> None:
    order = order_selectors.get_order(payload["order_id"])
    if not order.email or payload["to"] == "new":
        return
    body = render_to_string("notifications/order_status.txt", {
        "order": order, "status_url": f"{settings.SITE_URL}/orders/{order.public_token}",
    })
    tasks.send_email.delay(f"order-status-{order.pk}-{payload['to']}", order.email,
                           f"Замовлення {order.number}: {order.get_status_display()}", body)


def on_order_paid(payload: dict[str, Any]) -> None:
    order = order_selectors.get_order(payload["order_id"])
    tasks.send_telegram.delay(f"order-paid-{order.pk}",
                              f"Оплачено {order.number}: {format_uah(order.total_kop)}")


def on_payment_mismatch(payload: dict[str, Any]) -> None:
    order = order_selectors.get_order(payload["order_id"])
    tasks.send_telegram.delay(
        f"order-mismatch-{order.pk}-{payload['amount_kop']}",
        f"⚠️ Оплата {order.number} потребує перевірки: надійшло "
        f"{format_uah(payload['amount_kop'])}, очікувалось {format_uah(order.total_kop)}\n"
        f"{_admin_link(f'orders/order/{order.pk}/change/')}",
    )


def on_unconfirmed_reminder(payload: dict[str, Any]) -> None:
    order = order_selectors.get_order(payload["order_id"])
    tasks.send_telegram.delay(f"order-remind-{order.pk}",
                              f"Замовлення досі не підтверджене\n{_order_summary(order)}")


def on_lead_created(payload: dict[str, Any]) -> None:
    lead = lead_selectors.get_lead(payload["lead_id"])
    total = format_uah(lead.estimate.total_kop) if lead.estimate else "без кошторису"
    tasks.send_telegram.delay(
        f"lead-{lead.pk}",
        f"Нова заявка з калькулятора\n{escape(lead.name)}, {escape(lead.phone)}\n"
        f"Кошторис: {total}\n{_admin_link(f'leads/lead/{lead.pk}/change/')}",
    )


def on_import_finished(payload: dict[str, Any]) -> None:
    tasks.send_telegram.delay(
        f"import-{payload.get('new')}-{payload.get('updated')}-{payload.get('errors')}",
        f"Імпорт товарів завершено: нових {payload.get('new', 0)}, "
        f"оновлено {payload.get('updated', 0)}, помилок {payload.get('errors', 0)}",
    )


def register() -> None:
    subscribe(order_events.ORDER_CREATED, on_order_created)
    subscribe(order_events.ORDER_STATUS_CHANGED, on_status_changed)
    subscribe(order_events.ORDER_PAID, on_order_paid)
    subscribe(order_events.ORDER_PAYMENT_MISMATCH, on_payment_mismatch)
    subscribe(order_events.ORDER_UNCONFIRMED_REMINDER, on_unconfirmed_reminder)
    subscribe(LEAD_CREATED, on_lead_created)
    subscribe("catalog.import_finished", on_import_finished)
