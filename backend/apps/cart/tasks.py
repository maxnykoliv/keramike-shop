from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.cart.models import Cart


@shared_task
def cleanup_expired() -> int:
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Cart.objects.filter(expires_at__lt=cutoff).delete()
    return deleted
