from decimal import Decimal

from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.history import staff_history_user
from apps.core.models import TimeStampedModel


class Category(TimeStampedModel):
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT,
                               related_name="children", verbose_name="батьківська")
    slug = models.SlugField(unique=True)
    name = models.CharField("назва", max_length=200)
    sort = models.PositiveIntegerField("порядок", default=0)
    is_active = models.BooleanField("активна", default=True)

    class Meta:
        ordering = ["sort", "name"]
        verbose_name = "категорія"
        verbose_name_plural = "категорії"

    def __str__(self) -> str:
        return self.name


class Manufacturer(TimeStampedModel):
    name = models.CharField("назва", max_length=200)
    slug = models.SlugField(unique=True)
    country = models.CharField("країна", max_length=100, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "виробник"
        verbose_name_plural = "виробники"

    def __str__(self) -> str:
        return self.name


class Collection(TimeStampedModel):
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT,
                                     related_name="collections", verbose_name="виробник")
    name = models.CharField("назва", max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField("опис", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "колекція"
        verbose_name_plural = "колекції"

    def __str__(self) -> str:
        return f"{self.manufacturer} {self.name}"


class Product(TimeStampedModel):
    class Kind(models.TextChoices):
        TILE = "tile", "Плитка"
        MOSAIC = "mosaic", "Мозаїка"
        DECOR = "decor", "Декор"
        GLUE = "glue", "Клей"
        GROUT = "grout", "Затирка"
        PRIMER = "primer", "Ґрунтовка"
        WATERPROOFING = "waterproofing", "Гідроізоляція"
        ACCESSORY = "accessory", "Аксесуар"

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        ACTIVE = "active", "Активний"
        HIDDEN = "hidden", "Прихований"

    class Unit(models.TextChoices):
        M2 = "m2", "м²"
        PCS = "pcs", "шт"
        BAG = "bag", "мішок"
        BUCKET = "bucket", "відро"

    class StockStatus(models.TextChoices):
        IN_STOCK = "in_stock", "В наявності"
        ON_ORDER = "on_order", "Під замовлення"
        OUT_OF_STOCK = "out_of_stock", "Немає"

    sku = models.CharField("артикул", max_length=64, unique=True)
    slug = models.SlugField(max_length=220, unique=True)
    name = models.CharField("назва", max_length=255)
    kind = models.CharField("тип", max_length=20, choices=Kind.choices)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products",
                                 verbose_name="категорія")
    collection = models.ForeignKey(Collection, null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name="products", verbose_name="колекція")
    status = models.CharField("статус", max_length=10, choices=Status.choices,
                              default=Status.DRAFT)
    unit = models.CharField("одиниця ціни", max_length=10, choices=Unit.choices)
    price_kop = models.PositiveIntegerField("ціна, коп. за одиницю")
    old_price_kop = models.PositiveIntegerField("стара ціна, коп.", null=True, blank=True)
    master_price_kop = models.PositiveIntegerField(
        "ціна для майстрів, коп.", null=True, blank=True,
        help_text="Порожньо — майстер бачить звичайну ціну",
    )
    # Для плитки залишок у м², для решти в одиницях продажу.
    stock_qty = models.DecimalField("залишок", max_digits=12, decimal_places=3,
                                    default=Decimal("0"))
    reserved_qty = models.DecimalField("зарезервовано", max_digits=12, decimal_places=3,
                                       default=Decimal("0"))
    stock_status = models.CharField("наявність", max_length=20, choices=StockStatus.choices,
                                    default=StockStatus.IN_STOCK)
    weight_kg = models.DecimalField("вага одиниці, кг", max_digits=8, decimal_places=3,
                                    null=True, blank=True)
    description = models.TextField("опис", blank=True)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.CharField(max_length=500, blank=True)

    history = HistoricalRecords(get_user=staff_history_user)

    class Meta:
        ordering = ["name"]
        verbose_name = "товар"
        verbose_name_plural = "товари"
        indexes = [
            models.Index(fields=["status", "category"]),
            models.Index(fields=["price_kop"]),
            GinIndex(name="product_name_trgm", fields=["name"], opclasses=["gin_trgm_ops"]),
            GinIndex(name="product_sku_trgm", fields=["sku"], opclasses=["gin_trgm_ops"]),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(reserved_qty__gte=0),
                                   name="product_reserved_non_negative"),
            models.CheckConstraint(condition=models.Q(reserved_qty__lte=models.F("stock_qty")),
                                   name="product_reserved_lte_stock"),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.sku})"

    @property
    def available_qty(self) -> Decimal:
        return self.stock_qty - self.reserved_qty

    @property
    def is_tile(self) -> bool:
        return self.kind in {self.Kind.TILE, self.Kind.MOSAIC, self.Kind.DECOR} and hasattr(
            self, "tile_spec"
        )


class TileSpec(models.Model):
    class Material(models.TextChoices):
        CERAMIC = "ceramic", "Кераміка"
        PORCELAIN = "porcelain", "Керамограніт"

    class Application(models.TextChoices):
        WALL = "wall", "Стіна"
        FLOOR = "floor", "Підлога"
        OUTDOOR = "outdoor", "Вулиця"

    class Room(models.TextChoices):
        BATHROOM = "bathroom", "Ванна"
        TOILET = "toilet", "Туалет"
        KITCHEN = "kitchen", "Кухня"
        HALLWAY = "hallway", "Коридор"
        TERRACE = "terrace", "Тераса"
        LIVING = "living", "Житлова кімната"

    product = models.OneToOneField(Product, primary_key=True, on_delete=models.CASCADE,
                                   related_name="tile_spec")
    width_mm = models.PositiveIntegerField("ширина, мм")
    height_mm = models.PositiveIntegerField("довжина, мм")
    thickness_mm = models.PositiveIntegerField("товщина, мм", default=8)
    m2_per_pack = models.DecimalField("м² в упаковці", max_digits=8, decimal_places=3,
                                      null=True, blank=True)
    pcs_per_pack = models.PositiveIntegerField("шт в упаковці", null=True, blank=True)
    pack_weight_kg = models.DecimalField("вага упаковки, кг", max_digits=8, decimal_places=3,
                                         null=True, blank=True)
    material = models.CharField("матеріал", max_length=20, choices=Material.choices,
                                default=Material.CERAMIC)
    surface = models.CharField("поверхня", max_length=50, blank=True)
    color = models.CharField("колір", max_length=50, blank=True)
    applications = ArrayField(models.CharField(max_length=20, choices=Application.choices),
                              default=list, blank=True, verbose_name="призначення")
    rooms = ArrayField(models.CharField(max_length=20, choices=Room.choices),
                       default=list, blank=True, verbose_name="приміщення")

    history = HistoricalRecords(get_user=staff_history_user)

    class Meta:
        verbose_name = "характеристики плитки"
        verbose_name_plural = "характеристики плитки"
        indexes = [
            models.Index(fields=["width_mm", "height_mm"]),
            GinIndex(fields=["applications"], name="tilespec_applications_gin"),
            GinIndex(fields=["rooms"], name="tilespec_rooms_gin"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(models.Q(m2_per_pack__isnull=False)
                           | models.Q(pcs_per_pack__isnull=False)),
                name="tilespec_pack_defined",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.width_mm}×{self.height_mm}"

    @property
    def effective_m2_per_pack(self) -> Decimal:
        if self.m2_per_pack:
            return self.m2_per_pack
        area = Decimal(self.width_mm) * Decimal(self.height_mm) / Decimal(1_000_000)
        return (area * Decimal(self.pcs_per_pack or 0)).quantize(Decimal("0.001"))


class MaterialSpec(models.Model):
    class PackUnit(models.TextChoices):
        KG = "kg", "кг"
        L = "l", "л"

    product = models.OneToOneField(Product, primary_key=True, on_delete=models.CASCADE,
                                   related_name="material_spec")
    pack_size = models.DecimalField("обсяг упаковки", max_digits=8, decimal_places=3)
    pack_unit = models.CharField("одиниця", max_length=5, choices=PackUnit.choices)
    consumption_hint = models.CharField("підказка щодо витрати", max_length=255, blank=True)

    class Meta:
        verbose_name = "характеристики матеріалу"
        verbose_name_plural = "характеристики матеріалів"

    def __str__(self) -> str:
        return f"{self.pack_size} {self.get_pack_unit_display()}"


class ProductImage(TimeStampedModel):
    class Kind(models.TextChoices):
        PRODUCT = "product", "Товар"
        INTERIOR = "interior", "В інтер'єрі"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("файл", upload_to="products/%Y/%m/")
    kind = models.CharField("тип", max_length=10, choices=Kind.choices, default=Kind.PRODUCT)
    alt = models.CharField("опис для пошуковиків", max_length=255, blank=True)
    sort = models.PositiveIntegerField("порядок", default=0)
    # Зменшені копії WebP: {"sm": "...", "md": "...", "lg": "..."}
    variants = models.JSONField(default=dict, blank=True, editable=False)

    class Meta:
        ordering = ["sort", "id"]
        verbose_name = "фото"
        verbose_name_plural = "фото"


class ProductRelation(models.Model):
    class Type(models.TextChoices):
        SAME_COLLECTION = "same_collection", "Та сама колекція"
        RECOMMENDED = "recommended", "Супутній товар"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="relations")
    related = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="+",
                                verbose_name="пов'язаний товар")
    type = models.CharField("тип", max_length=20, choices=Type.choices)

    class Meta:
        verbose_name = "пов'язаний товар"
        verbose_name_plural = "пов'язані товари"
        constraints = [
            models.UniqueConstraint(fields=["product", "related", "type"],
                                    name="unique_product_relation"),
        ]

    def __str__(self) -> str:
        return f"{self.product} → {self.related}"
