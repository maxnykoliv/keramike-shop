"""Зміни в каталозі: статуси, резерв і списання залишків, скидання кешу."""

from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from apps.catalog.models import Product
from apps.catalog.selectors import CACHE_VERSION_KEY, catalog_cache_version
from apps.core.exceptions import NotFound, OutOfStock

REVALIDATE_LOCK_KEY = "catalog:revalidate"
REVALIDATE_DELAY = 10  # секунд


def invalidate_cache() -> None:
    catalog_cache_version()
    try:
        cache.incr(CACHE_VERSION_KEY)
    except ValueError:
        cache.set(CACHE_VERSION_KEY, 2, timeout=None)
    # Імпорт зберігає товари по одному: сайт просимо оновитися раз після серії змін.
    if settings.REVALIDATE_SECRET and cache.add(REVALIDATE_LOCK_KEY, 1, REVALIDATE_DELAY):
        from apps.catalog.tasks import revalidate_site

        revalidate_site.apply_async(countdown=REVALIDATE_DELAY)


def set_status(product: Product, status: str) -> Product:
    product.status = status
    product.save(update_fields=["status", "updated_at"])
    return product


def _lock(product_id: int) -> Product:
    product = Product.objects.select_for_update().filter(id=product_id).first()
    if product is None:
        raise NotFound("Товар не знайдено")
    return product


@transaction.atomic
def reserve(product_id: int, units: Decimal) -> Decimal:
    """Резервує залишок. Повертає зарезервовану кількість: 0 для товару під замовлення."""
    product = _lock(product_id)
    if product.stock_status == Product.StockStatus.ON_ORDER:
        return Decimal("0")
    if product.available_qty < units:
        raise OutOfStock(
            f"Недостатньо «{product.name}»: доступно {product.available_qty}, потрібно {units}",
            extra={"sku": product.sku},
        )
    product.reserved_qty += units
    product.save(update_fields=["reserved_qty", "updated_at"])
    return units


@transaction.atomic
def release(product_id: int, units: Decimal) -> None:
    if units <= 0:
        return
    product = _lock(product_id)
    product.reserved_qty = max(Decimal("0"), product.reserved_qty - units)
    product.save(update_fields=["reserved_qty", "updated_at"])


@transaction.atomic
def write_off(product_id: int, reserved: Decimal) -> None:
    """Списує зарезервований товар після відправлення."""
    if reserved <= 0:
        return
    product = _lock(product_id)
    product.reserved_qty = max(Decimal("0"), product.reserved_qty - reserved)
    product.stock_qty = max(Decimal("0"), product.stock_qty - reserved)
    product.save(update_fields=["reserved_qty", "stock_qty", "updated_at"])
