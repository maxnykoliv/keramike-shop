from decimal import Decimal

from django.db import transaction

from apps.calc.models import Estimate
from apps.core import events
from apps.core.exceptions import DomainError
from apps.leads.models import Lead
from apps.orders import services as order_services
from apps.orders.models import Order
from apps.orders.state import DeliveryMethod, PaymentMethod

LEAD_CREATED = "lead.created"


@transaction.atomic
def create_lead(*, name: str, phone: str, comment: str = "",
                estimate: Estimate | None = None) -> Lead:
    lead = Lead.objects.create(name=name, phone=phone, comment=comment, estimate=estimate)
    events.publish(LEAD_CREATED, {"lead_id": lead.pk})
    return lead


@transaction.atomic
def convert_to_order(lead_id: int, *, actor=None) -> Order:
    """Creates an order from an estimate's products. The manager settles delivery and payment."""
    lead = (Lead.objects.select_for_update(of=("self",)).select_related("estimate")
            .get(pk=lead_id))
    if lead.order_id:
        raise DomainError("Замовлення для цієї заявки вже створено")
    if lead.estimate is None:
        raise DomainError("У заявці немає кошторису")
    requests = [
        order_services.LineRequest(product_id=line["product_id"],
                                   qty=int(Decimal(line["quantity"])),
                                   group_label=f"Кошторис {lead.estimate.public_code}")
        for line in lead.estimate.result["lines"]
        if line.get("product_id") and line["kind"] != "labor"
    ]
    if not requests:
        raise DomainError("У кошторисі немає товарів з каталогу")
    order = order_services.create_order(
        customer=order_services.Customer(name=lead.name, phone=lead.phone,
                                         comment=lead.comment),
        delivery_method=DeliveryMethod.PICKUP,
        delivery={},
        payment_method=PaymentMethod.COD,
        lines=order_services.build_lines(requests, require_available=False),
        delivery_kop=None,
        estimate_id=lead.estimate_id,
        actor=actor,
    )
    lead.order = order
    lead.status = Lead.Status.CONVERTED
    lead.manager = lead.manager or actor
    lead.save()
    return order
