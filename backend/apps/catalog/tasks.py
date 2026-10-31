import io
from pathlib import PurePosixPath

import requests
import structlog
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, UnidentifiedImageError

from apps.catalog.models import ProductImage

logger = structlog.get_logger(__name__)
SIZES = {"sm": 320, "md": 800, "lg": 1600}


@shared_task(max_retries=3, default_retry_delay=60)
def process_image(image_id: int) -> dict[str, str]:
    """Робить WebP у трьох розмірах. Повторний запуск перезаписує ті самі файли."""
    image = ProductImage.objects.filter(pk=image_id).first()
    if image is None or not image.image:
        return {}
    source: Image.Image
    try:
        with image.image.open("rb") as fh:
            source = Image.open(io.BytesIO(fh.read()))
            source.load()
    except (UnidentifiedImageError, OSError):
        logger.warning("image_unreadable", image_id=image_id)
        return {}

    source = source.convert("RGB")
    stem = PurePosixPath(image.image.name or f"image-{image_id}").stem
    variants: dict[str, str] = {}
    for key, max_side in SIZES.items():
        copy = source.copy()
        copy.thumbnail((max_side, max_side))
        buffer = io.BytesIO()
        copy.save(buffer, format="WEBP", quality=82)
        name = f"products/variants/{image_id}/{stem}_{key}.webp"
        if default_storage.exists(name):
            default_storage.delete(name)
        variants[key] = default_storage.save(name, ContentFile(buffer.getvalue()))
    ProductImage.objects.filter(pk=image_id).update(variants=variants)
    return variants


@shared_task
def revalidate_site(tag: str = "catalog") -> bool:
    """Скидає кеш сторінок каталогу на сайті, щоб нові ціни з'явилися одразу."""
    try:
        response = requests.post(f"{settings.SITE_URL}/api/revalidate", json={"tag": tag},
                                 headers={"X-Revalidate-Secret": settings.REVALIDATE_SECRET},
                                 timeout=10)
    except requests.RequestException:
        logger.warning("site_revalidate_unavailable")
        return False
    if response.status_code != 200:
        logger.warning("site_revalidate_failed", status=response.status_code)
        return False
    return True
