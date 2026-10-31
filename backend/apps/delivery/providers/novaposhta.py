"""Клієнт API Нової пошти 2.0."""

from decimal import Decimal
from typing import Any

import requests
import structlog
from django.conf import settings

from apps.core.exceptions import ProviderUnavailable

logger = structlog.get_logger(__name__)


class NovaPoshtaClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else settings.NOVA_POSHTA_API_KEY
        self.url = settings.NOVA_POSHTA_API_URL

    def call(self, model: str, method: str, props: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.api_key:
            raise ProviderUnavailable("Нова пошта не налаштована")
        body = {"apiKey": self.api_key, "modelName": model, "calledMethod": method,
                "methodProperties": props}
        try:
            response = requests.post(self.url, json=body, timeout=10)
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("novaposhta_unavailable", method=method)
            raise ProviderUnavailable("Нова пошта тимчасово недоступна") from exc
        if not payload.get("success"):
            logger.warning("novaposhta_error", method=method, errors=payload.get("errors"))
            raise ProviderUnavailable("; ".join(payload.get("errors") or ["Помилка Нової пошти"]))
        return payload.get("data") or []

    def search_cities(self, query: str, limit: int = 20) -> list[dict[str, str]]:
        data = self.call("Address", "searchSettlements",
                         {"CityName": query, "Limit": str(limit), "Page": "1"})
        addresses = data[0].get("Addresses", []) if data else []
        return [
            {"ref": item["DeliveryCity"], "name": item["Present"]}
            for item in addresses if item.get("DeliveryCity")
        ]

    def warehouses(self, city_ref: str, query: str = "") -> list[dict[str, str]]:
        data = self.call("AddressGeneral", "getWarehouses",
                         {"CityRef": city_ref, "FindByString": query, "Limit": "500"})
        return [
            {"ref": item["Ref"], "name": item["Description"],
             "number": item.get("Number", ""), "type": item.get("CategoryOfWarehouse", "")}
            for item in data
        ]

    def price(self, *, city_sender: str, city_recipient: str, weight_kg: Decimal,
              declared_uah: Decimal) -> Decimal:
        data = self.call("InternetDocument", "getDocumentPrice", {
            "CitySender": city_sender,
            "CityRecipient": city_recipient,
            "Weight": str(max(weight_kg, Decimal("0.1"))),
            "ServiceType": "WarehouseWarehouse",
            "Cost": str(declared_uah),
            "CargoType": "Cargo",
            "SeatsAmount": "1",
        })
        return Decimal(str(data[0]["Cost"]))

    def create_document(self, props: dict[str, Any]) -> dict[str, Any]:
        data = self.call("InternetDocument", "save", props)
        return data[0]

    def tracking(self, ttns: list[str]) -> list[dict[str, Any]]:
        documents = [{"DocumentNumber": ttn} for ttn in ttns]
        return self.call("TrackingDocument", "getStatusDocuments", {"Documents": documents})
