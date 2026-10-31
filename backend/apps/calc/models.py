from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Max, Q
from simple_history.models import HistoricalRecords

from apps.core.history import staff_history_user
from apps.core.models import TimeStampedModel


def default_waste() -> dict[str, str]:
    return {"straight": "0.10", "offset": "0.12", "diagonal": "0.15", "herringbone": "0.20"}


def default_glue() -> dict[str, str]:
    return {"small": "3.5", "medium": "5", "large": "7"}


class CalcSettings(TimeStampedModel):
    """Версія налаштувань калькулятора.

    Опублікована версія незмінна, правки — через нову чернетку.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PUBLISHED = "published", "Опублікована"
        ARCHIVED = "archived", "Архівна"

    version = models.PositiveIntegerField("версія", unique=True, editable=False)
    status = models.CharField("статус", max_length=10, choices=Status.choices,
                              default=Status.DRAFT, editable=False)
    waste_by_layout = models.JSONField("запас за способом укладання", default=default_waste)
    glue_kg_per_m2 = models.JSONField("клей, кг/м² за розміром плитки", default=default_glue)
    grout_density = models.DecimalField("густина затирки", max_digits=4, decimal_places=2,
                                        default=Decimal("1.5"))
    primer_l_per_m2 = models.DecimalField("ґрунтовка, л/м²", max_digits=5, decimal_places=3,
                                          default=Decimal("0.2"))
    waterproofing_kg_per_m2 = models.DecimalField("гідроізоляція, кг/м²", max_digits=5,
                                                  decimal_places=3, default=Decimal("1.5"))
    glue_product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="+",
                                     limit_choices_to={"kind": "glue"}, verbose_name="клей")
    grout_product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                      on_delete=models.SET_NULL, related_name="+",
                                      limit_choices_to={"kind": "grout"}, verbose_name="затирка")
    primer_product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="+",
                                       limit_choices_to={"kind": "primer"},
                                       verbose_name="ґрунтовка")
    waterproofing_product = models.ForeignKey("catalog.Product", null=True, blank=True,
                                              on_delete=models.SET_NULL, related_name="+",
                                              limit_choices_to={"kind": "waterproofing"},
                                              verbose_name="гідроізоляція")
    published_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                     on_delete=models.SET_NULL, related_name="+",
                                     editable=False, verbose_name="опублікував")
    published_at = models.DateTimeField("опубліковано", null=True, blank=True, editable=False)

    history = HistoricalRecords(get_user=staff_history_user)

    class Meta:
        ordering = ["-version"]
        verbose_name = "налаштування калькулятора"
        verbose_name_plural = "налаштування калькулятора"
        constraints = [
            models.UniqueConstraint(fields=["status"], condition=Q(status="published"),
                                    name="calc_single_published_settings"),
        ]

    def __str__(self) -> str:
        return f"Версія {self.version} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.version:
            last = CalcSettings.objects.aggregate(last=Max("version"))["last"] or 0
            self.version = last + 1
        super().save(*args, **kwargs)


class LaborRate(TimeStampedModel):
    class Surface(models.TextChoices):
        FLOOR = "floor", "Підлога"
        WALLS = "walls", "Стіни"

    class SizeClass(models.TextChoices):
        SMALL = "small", "До 30 см"
        MEDIUM = "medium", "30–60 см"
        LARGE = "large", "Понад 60 см"

    surface = models.CharField("поверхня", max_length=10, choices=Surface.choices)
    size_class = models.CharField("розмір плитки", max_length=10, choices=SizeClass.choices)
    price_kop_per_m2 = models.PositiveIntegerField("ціна, коп./м²")

    history = HistoricalRecords(get_user=staff_history_user)

    class Meta:
        ordering = ["surface", "size_class"]
        verbose_name = "тариф робіт"
        verbose_name_plural = "тарифи робіт"
        constraints = [
            models.UniqueConstraint(fields=["surface", "size_class"], name="unique_labor_rate"),
        ]

    def __str__(self) -> str:
        return f"{self.get_surface_display()}, {self.get_size_class_display()}"


class Estimate(TimeStampedModel):
    class Source(models.TextChoices):
        CALCULATOR = "calculator", "Калькулятор"
        PRODUCT_CARD = "product_card", "Картка товару"
        ADMIN = "admin", "Адмінка"

    public_code = models.CharField("код", max_length=8, unique=True, editable=False)
    input = models.JSONField("ввід")
    result = models.JSONField("результат")
    settings = models.ForeignKey(CalcSettings, on_delete=models.PROTECT,
                                 related_name="estimates", verbose_name="версія налаштувань")
    total_kop = models.PositiveIntegerField("разом, коп.")
    source = models.CharField("джерело", max_length=20, choices=Source.choices,
                              default=Source.CALCULATOR)
    pdf = models.FileField("PDF", upload_to="estimates/", blank=True)
    customer = models.ForeignKey("customers.Customer", null=True, blank=True,
                                 on_delete=models.SET_NULL, related_name="estimates",
                                 verbose_name="клієнт")
    title = models.CharField("назва", max_length=120, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "кошторис"
        verbose_name_plural = "кошториси"

    def __str__(self) -> str:
        return self.public_code
