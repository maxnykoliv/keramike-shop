from apps.core.exceptions import NotFound
from apps.leads.models import Lead


def get_lead(lead_id: int) -> Lead:
    lead = Lead.objects.select_related("estimate").filter(pk=lead_id).first()
    if lead is None:
        raise NotFound("Заявку не знайдено")
    return lead
