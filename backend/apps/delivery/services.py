"""Довідники й вартість доставки, ТТН, синхронізація статусів посилок."""

import secrets
from decimal import Decimal
from typing import Any

import structlog
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.cart.selectors import cart_view, get_cart
from apps.core.exceptions import DomainError
from apps.core.money import kop_to_uah, uah_to_kop
from apps.delivery.models import DeliverySettings, Shipment
from apps.delivery.providers.novaposhta import NovaPoshtaClient
from apps.orders import selectors as order_selectors
from apps.orders import services as order_services
from apps.orders.state import DeliveryMethod, OrderStatus

logger = structlog.get_logger(__name__)

DIRECTORY_TTL = 60 * 60 * 24
QUOTE_TTL = 60 * 30
# Коди статусів Нової пошти: 9, 10, 11 — отримано; 102, 103, 108 — повернення/відмова.
NP_DELIVERED = {"9", "10", "11"}
NP_RETURNED = {"102", "103", "108"}


def search_cities(query: str) -> list[dict[str, str]]:
    key = f"np:cities:{query.strip().lower()}"
    cities = cache.get(key)
    if cities is None:
        cities = NovaPoshtaClient().search_cities(query)
        cache.set(key, cities, DIRECTORY_TTL)
    return cities


def warehouses(city_ref: str, query: str = "") -> list[dict[str, str]]:
    key = f"np:warehouses:{city_ref}"
    items = cache.get(key)
    if items is None:
        items = NovaPoshtaClient().warehouses(city_ref)
        cache.set(key, items, DIRECTORY_TTL)
    if query:
        needle = query.lower()
        items = [w for w in items if needle in w["name"].lower() or needle == w["number"]]
    return items


def quote(*, method: str, cart_token: str, city_ref: str = "") -> dict[str, Any]:
    """Рахує доставку для кошика й кладе результат у кеш. Оформлення бере його за quote_id."""
    view = cart_view(get_cart(cart_token))
    cost_kop: int | None
    if method == DeliveryMethod.PICKUP:
        cost_kop = 0
    elif method == DeliveryMethod.LOCAL:
        cost_kop = DeliverySettings.load().local_delivery_kop
    elif method == DeliveryMethod.NOVA_POSHTA:
        if not city_ref:
            raise DomainError("Оберіть місто", field="city_ref")
        sender_city = DeliverySettings.load().np_sender_city_ref
        if not sender_city:
            cost_kop = None
        else:
            cost = NovaPoshtaClient().price(
                city_sender=sender_city, city_recipient=city_ref, weight_kg=view.weight_kg,
                declared_uah=kop_to_uah(view.subtotal_kop),
            )
            cost_kop = uah_to_kop(cost)
    else:
        raise DomainError("Невідомий спосіб доставки", field="method")

    quote_id = secrets.token_urlsafe(12)
    data = {"quote_id": quote_id, "method": method, "city_ref": city_ref,
            "cart_token": cart_token, "cost_kop": cost_kop, "weight_kg": str(view.weight_kg)}
    cache.set(f"delivery:quote:{quote_id}", data, QUOTE_TTL)
    return data


def cached_quote(quote_id: str | None, *, method: str, cart_token: str) -> int | None:
    """Вартість, яку клієнт бачив. None — «уточнюється менеджером»."""
    if method == DeliveryMethod.PICKUP:
        return 0
    if not quote_id:
        return None
    data = cache.get(f"delivery:quote:{quote_id}")
    if not data or data["method"] != method or data["cart_token"] != cart_token:
        return None
    return data["cost_kop"]


def on_order_status_changed(payload: dict[str, Any]) -> None:
    """Зібране замовлення Новою поштою отримує чернетку відправлення."""
    if payload.get("to") != OrderStatus.PACKED:
        return
    order = order_selectors.get_order(payload["order_id"])
    if order.delivery_method != DeliveryMethod.NOVA_POSHTA:
        return
    Shipment.objects.get_or_create(
        order=order, carrier=Shipment.Carrier.NOVA_POSHTA,
        status=Shipment.Status.DRAFT,
    )


@transaction.atomic
def create_ttn(shipment_id: int) -> Shipment:
    shipment = Shipment.objects.select_for_update().select_related("order").get(pk=shipment_id)
    if shipment.status != Shipment.Status.DRAFT:
        raise DomainError("ТТН уже створено")
    order = shipment.order
    config = DeliverySettings.load()
    if not (config.np_sender_ref and config.np_sender_contact_ref
            and config.np_sender_warehouse_ref):
        raise DomainError("Заповніть дані відправника в налаштуваннях доставки")
    recipient = order.delivery or {}
    document = NovaPoshtaClient().create_document({
        "PayerType": "Recipient",
        "PaymentMethod": "Cash",
        "CargoType": "Cargo",
        "ServiceType": "WarehouseWarehouse",
        "SeatsAmount": "1",
        "Weight": str(max(order.weight_kg, Decimal("0.1"))),
        "Cost": str(kop_to_uah(order.subtotal_kop)),
        "Description": f"Замовлення {order.number}",
        "DateTime": timezone.localdate().strftime("%d.%m.%Y"),
        "Sender": config.np_sender_ref,
        "ContactSender": config.np_sender_contact_ref,
        "CitySender": config.np_sender_city_ref,
        "SenderAddress": config.np_sender_warehouse_ref,
        "SendersPhone": config.np_sender_phone,
        "RecipientCityRef": recipient.get("city_ref", ""),
        "RecipientAddress": recipient.get("warehouse_ref", ""),
        "RecipientName": order.customer_name,
        "RecipientsPhone": order.phone,
        "NewAddress": "1",
    })
    shipment.ttn = document["IntDocNumber"]
    shipment.cost_kop = uah_to_kop(Decimal(str(document.get("CostOnSite", "0"))))
    shipment.status = Shipment.Status.CREATED
    shipment.raw = document
    shipment.save()
    return shipment


def sync_parcel_statuses() -> int:
    active = list(Shipment.objects.filter(
        carrier=Shipment.Carrier.NOVA_POSHTA,
        status__in=[Shipment.Status.CREATED, Shipment.Status.IN_TRANSIT],
    ).exclude(ttn=""))
    if not active:
        return 0
    by_ttn = {s.ttn: s for s in active}
    updated = 0
    for item in NovaPoshtaClient().tracking(list(by_ttn)):
        shipment = by_ttn.get(str(item.get("Number", "")))
        if shipment is None:
            continue
        code = str(item.get("StatusCode"))
        if code in NP_DELIVERED:
            new_status = Shipment.Status.DELIVERED
        elif code in NP_RETURNED:
            new_status = Shipment.Status.RETURNED
        else:
            new_status = Shipment.Status.IN_TRANSIT
        if new_status == shipment.status:
            continue
        shipment.status = new_status
        shipment.save(update_fields=["status", "updated_at"])
        updated += 1
        if new_status == Shipment.Status.DELIVERED:
            try:
                order_services.transition(shipment.order_id, OrderStatus.COMPLETED,
                                          comment=f"Отримано, ТТН {shipment.ttn}")
            except DomainError:
                logger.info("order_not_completed", order_id=shipment.order_id)
    return updated
