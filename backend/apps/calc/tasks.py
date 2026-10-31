import structlog
from celery import shared_task
from django.core.files.base import ContentFile
from django.template.loader import render_to_string

from apps.calc.models import Estimate
from apps.core.money import format_uah

logger = structlog.get_logger(__name__)

UNITS = {"pack": "уп.", "m2": "м²", "kg": "кг", "l": "л"}


@shared_task(max_retries=3, default_retry_delay=30)
def render_estimate_pdf(estimate_id: int) -> str | None:
    estimate = Estimate.objects.filter(pk=estimate_id).first()
    if estimate is None or estimate.pdf:
        return estimate.pdf.name if estimate else None
    try:
        from weasyprint import HTML
    except (ImportError, OSError):
        logger.error("weasyprint_unavailable", estimate=estimate.public_code)
        return None

    lines = [
        {**line, "unit_label": UNITS.get(line["unit"], line["unit"]),
         "base_unit_label": UNITS.get(line["base_unit"], line["base_unit"]),
         "total": format_uah(line["total_kop"])}
        for line in estimate.result["lines"]
    ]
    html = render_to_string("calc/estimate_pdf.html", {
        "estimate": estimate,
        "lines": lines,
        "total": format_uah(estimate.total_kop),
        "warnings": estimate.result.get("warnings", []),
    })
    pdf = HTML(string=html).write_pdf()
    estimate.pdf.save(f"{estimate.public_code}.pdf", ContentFile(pdf), save=True)
    return estimate.pdf.name
