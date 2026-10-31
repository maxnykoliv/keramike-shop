from celery import shared_task

from apps.delivery import services


@shared_task
def sync_parcel_statuses() -> int:
    return services.sync_parcel_statuses()
