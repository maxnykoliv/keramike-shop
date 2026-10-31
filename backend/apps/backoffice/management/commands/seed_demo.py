"""Демо-дані для локальної розробки: ролі, власник, каталог, матеріали, налаштування калькулятора.

Безпечно запускати повторно. Не для production.
"""

import json
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.calc.models import CalcSettings, LaborRate
from apps.catalog.models import Category, Collection, Manufacturer, MaterialSpec, Product, TileSpec
from apps.core.roles import OWNER_GROUP
from apps.customers.models import Customer

CALC_SETTINGS = Path(settings.BASE_DIR).parent / "calc-cases" / "settings.json"

TILES = [
    ("CRS-MG-6060", "Marble Grey 60×60", 600, 600, "1.44", None, "32", 65000,
     ["floor", "wall"], ["bathroom", "kitchen", "hallway"], "сірий", "матова"),
    ("CRS-WW-3060", "White Wave 30×60", 300, 600, None, 8, "24", 52000,
     ["wall"], ["bathroom", "toilet", "kitchen"], "білий", "глянцева"),
    ("CRS-OAK-12060", "Oak Natural 120×60", 1200, 600, "1.44", None, "34", 98000,
     ["floor"], ["living", "hallway"], "бежевий", "структурована"),
    ("CRS-HEX-2020", "Hexagon Mint 20×20", 200, 200, None, 25, "18", 30000,
     ["floor", "wall"], ["toilet", "bathroom"], "м'ятний", "матова"),
]


class Command(BaseCommand):
    help = "Заповнює базу демо-даними"

    def add_arguments(self, parser):
        parser.add_argument("--owner-email", default="owner@example.com")
        parser.add_argument("--owner-password", default="")
        parser.add_argument("--extra-products", type=int, default=0,
                            help="Додаткові однотипні плитки — перевірити пагінацію каталогу")

    @transaction.atomic
    def handle(self, *args, owner_email: str, owner_password: str, extra_products: int,
               **options) -> None:
        if not settings.DEBUG:
            raise CommandError("seed_demo працює лише з DEBUG=True")
        call_command("setup_roles", verbosity=0)

        User = get_user_model()
        owner, created = User.objects.get_or_create(email=owner_email,
                                                    defaults={"is_staff": True})
        if created:
            if not owner_password:
                raise CommandError("Вкажіть --owner-password для нового власника")
            owner.set_password(owner_password)
            owner.save()
        owner.groups.add(Group.objects.get(name=OWNER_GROUP))

        tiles_cat, _ = Category.objects.get_or_create(slug="plytka", defaults={"name": "Плитка"})
        materials_cat, _ = Category.objects.get_or_create(
            slug="materialy", defaults={"name": "Матеріали для укладання"})
        maker, _ = Manufacturer.objects.get_or_create(
            slug="cersanit", defaults={"name": "Cersanit", "country": "Польща"})
        collection, _ = Collection.objects.get_or_create(
            slug="demo", defaults={"name": "Demo", "manufacturer": maker})

        for (sku, name, w, h, m2, pcs, weight, price, apps_, rooms, color, surface) in TILES:
            product, _ = Product.objects.update_or_create(sku=sku, defaults={
                "slug": sku.lower(), "name": name, "kind": Product.Kind.TILE,
                "category": tiles_cat, "collection": collection,
                "status": Product.Status.ACTIVE, "unit": Product.Unit.M2,
                "price_kop": price, "master_price_kop": price * 85 // 100,
                "stock_qty": Decimal("200"),
            })
            TileSpec.objects.update_or_create(product=product, defaults={
                "width_mm": w, "height_mm": h, "thickness_mm": 8,
                "m2_per_pack": Decimal(m2) if m2 else None, "pcs_per_pack": pcs,
                "pack_weight_kg": Decimal(weight), "applications": apps_, "rooms": rooms,
                "color": color, "surface": surface,
            })

        for i in range(1, extra_products + 1):
            product, _ = Product.objects.update_or_create(sku=f"CRS-EXT-{i:03d}", defaults={
                "slug": f"crs-ext-{i:03d}", "name": f"Stone Line {i:03d} 30×30",
                "kind": Product.Kind.TILE, "category": tiles_cat, "collection": collection,
                "status": Product.Status.ACTIVE, "unit": Product.Unit.M2,
                "price_kop": 40000 + i * 100, "stock_qty": Decimal("50"),
            })
            TileSpec.objects.update_or_create(product=product, defaults={
                "width_mm": 300, "height_mm": 300, "thickness_mm": 8,
                "m2_per_pack": Decimal("1.08"), "pack_weight_kg": Decimal("20"),
                "applications": ["floor"], "rooms": ["terrace"],
                "color": "сірий", "surface": "матова",
            })

        data = json.loads(CALC_SETTINGS.read_text())
        kinds = {"glue": Product.Kind.GLUE, "grout": Product.Kind.GROUT,
                 "primer": Product.Kind.PRIMER, "waterproofing": Product.Kind.WATERPROOFING}
        materials = {}
        for key, item in data["materials"].items():
            product, _ = Product.objects.update_or_create(sku=f"MAT-{key.upper()}", defaults={
                "slug": f"mat-{key}", "name": item["name"], "kind": kinds[key],
                "category": materials_cat, "status": Product.Status.ACTIVE,
                "unit": Product.Unit.BUCKET if key == "primer" else Product.Unit.BAG,
                "price_kop": item["price_kop"], "weight_kg": Decimal(item["pack_weight_kg"]),
                "stock_qty": Decimal("500"),
            })
            unit = MaterialSpec.PackUnit.L if key == "primer" else MaterialSpec.PackUnit.KG
            MaterialSpec.objects.update_or_create(product=product, defaults={
                "pack_size": Decimal(item["pack_size"]), "pack_unit": unit,
            })
            materials[key] = product

        for surface, rates in data["labor_kop_per_m2"].items():
            for size_class, price in rates.items():
                LaborRate.objects.update_or_create(surface=surface, size_class=size_class,
                                                   defaults={"price_kop_per_m2": price})

        if not CalcSettings.objects.filter(status=CalcSettings.Status.PUBLISHED).exists():
            CalcSettings.objects.create(
                status=CalcSettings.Status.PUBLISHED,
                waste_by_layout=data["waste_by_layout"],
                glue_kg_per_m2=data["glue_kg_per_m2"],
                grout_density=Decimal(data["grout_density"]),
                primer_l_per_m2=Decimal(data["primer_l_per_m2"]),
                waterproofing_kg_per_m2=Decimal(data["waterproofing_kg_per_m2"]),
                glue_product=materials["glue"], grout_product=materials["grout"],
                primer_product=materials["primer"],
                waterproofing_product=materials["waterproofing"],
            )
        Customer.objects.get_or_create(phone="+380670000001",
                                       defaults={"name": "Демо-майстер", "is_master": True})
        self.stdout.write(self.style.SUCCESS(
            f"Демо-дані готові. Власник: {owner_email}. Товарів: {Product.objects.count()}"
        ))
