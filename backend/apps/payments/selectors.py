from apps.payments.models import Payment


def latest_payment(order_id: int) -> Payment | None:
    return Payment.objects.filter(order_id=order_id).order_by("-created_at").first()
