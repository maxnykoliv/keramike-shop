"""Інфраструктурні сигнали: скидання кешу каталогу і обробка фото. Доменних дій тут немає."""

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.catalog.models import (
    Category,
    Collection,
    Manufacturer,
    MaterialSpec,
    Product,
    ProductImage,
    ProductRelation,
    TileSpec,
)
from apps.catalog.services import invalidate_cache

CACHED_MODELS = (Category, Manufacturer, Collection, Product, TileSpec, MaterialSpec,
                 ProductImage, ProductRelation)


def _invalidate(**kwargs) -> None:
    transaction.on_commit(invalidate_cache)


for model in CACHED_MODELS:
    post_save.connect(_invalidate, sender=model,
                      dispatch_uid=f"catalog-cache-save-{model.__name__}")
    post_delete.connect(_invalidate, sender=model,
                        dispatch_uid=f"catalog-cache-delete-{model.__name__}")


@receiver(post_save, sender=ProductImage, dispatch_uid="catalog-process-image")
def schedule_image_processing(sender, instance: ProductImage, created: bool, update_fields=None,
                              **kwargs) -> None:
    if update_fields and set(update_fields) <= {"variants"}:
        return
    from apps.catalog.tasks import process_image

    transaction.on_commit(lambda: process_image.delay(instance.pk))
