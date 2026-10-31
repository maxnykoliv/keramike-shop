from celery import shared_task

from apps.orders import selectors, services


@shared_task
def remind_unconfirmed() -> int:
    ids = list(selectors.unconfirmed_for_reminder().values_list("id", flat=True))
    for order_id in ids:
        services.mark_reminded(order_id)
    return len(ids)
