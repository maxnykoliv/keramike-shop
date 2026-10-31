"""Створює групи «Власник» і «Менеджер» з потрібними правами. Безпечно запускати повторно."""

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from apps.core.roles import MANAGER_GROUP, OWNER_GROUP

PROJECT_APPS = ["accounts", "customers", "catalog", "calc", "cart", "orders", "payments",
                "delivery", "leads"]

# Менеджер: замовлення, заявки, відправлення, описи товарів. Без цін, калькулятора, персоналу.
MANAGER_PERMISSIONS = {
    "orders": ["view_order", "change_order", "view_orderitem", "change_orderitem",
               "add_orderitem", "delete_orderitem", "view_orderevent"],
    "leads": ["view_lead", "change_lead"],
    "delivery": ["view_shipment", "change_shipment", "add_shipment"],
    "payments": ["view_payment"],
    "catalog": ["view_product", "change_product", "view_category", "view_collection",
                "view_manufacturer", "view_productimage", "add_productimage",
                "change_productimage", "view_tilespec", "change_tilespec"],
    "calc": ["view_estimate"],
    "cart": ["view_cart"],
    "customers": ["view_customer", "change_customer", "view_customeraddress",
                  "change_customeraddress", "view_customersession", "delete_customersession"],
}


class Command(BaseCommand):
    help = "Створює ролі персоналу"

    def handle(self, *args, **options) -> None:
        owner, _ = Group.objects.get_or_create(name=OWNER_GROUP)
        owner.permissions.set(
            Permission.objects.filter(content_type__app_label__in=PROJECT_APPS)
        )

        manager, _ = Group.objects.get_or_create(name=MANAGER_GROUP)
        perms: list[Permission] = []
        for app_label, codenames in MANAGER_PERMISSIONS.items():
            perms.extend(
                Permission.objects.filter(
                    content_type__app_label=app_label, codename__in=codenames
                )
            )
        manager.permissions.set(perms)
        self.stdout.write(self.style.SUCCESS(
            f"Ролі готові: {OWNER_GROUP} ({owner.permissions.count()} прав), "
            f"{MANAGER_GROUP} ({manager.permissions.count()} прав)"
        ))
