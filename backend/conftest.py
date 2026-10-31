import json
from decimal import Decimal
from pathlib import Path

import factory
import pytest
import responses
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.calc.models import CalcSettings, LaborRate
from apps.catalog.models import Category, MaterialSpec, Product, TileSpec

CALC_CASES = Path(__file__).resolve().parent.parent / "calc-cases"
TELEGRAM_URL = "https://api.telegram.org/bottest-token/sendMessage"
LOGIN_BOT_URL = "https://api.telegram.org/botlogin-token/sendMessage"


class CategoryFactory(factory.django.DjangoModelFactory[Category]):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Категорія {n}")
    slug = factory.Sequence(lambda n: f"category-{n}")


class ProductFactory(factory.django.DjangoModelFactory[Product]):
    class Meta:
        model = Product

    sku = factory.Sequence(lambda n: f"SKU-{n:05d}")
    slug = factory.Sequence(lambda n: f"product-{n}")
    name = factory.Sequence(lambda n: f"Товар {n}")
    kind = Product.Kind.ACCESSORY
    category = factory.SubFactory(CategoryFactory)
    status = Product.Status.ACTIVE
    unit = Product.Unit.PCS
    price_kop = 10000
    stock_qty = Decimal("100")
    weight_kg = Decimal("1")


def make_tile(*, width=600, height=600, price_kop=65000, m2_per_pack="1.44",
              pcs_per_pack=None, pack_weight="32", stock="100", applications=("floor", "wall"),
              **product_kwargs) -> Product:
    product = ProductFactory.create(
        kind=Product.Kind.TILE, unit=Product.Unit.M2, price_kop=price_kop,
        stock_qty=Decimal(stock), weight_kg=None, **product_kwargs,
    )
    TileSpec.objects.create(
        product=product, width_mm=width, height_mm=height, thickness_mm=8,
        m2_per_pack=Decimal(m2_per_pack) if m2_per_pack else None, pcs_per_pack=pcs_per_pack,
        pack_weight_kg=Decimal(pack_weight), applications=list(applications),
        color="сірий", surface="матова",
    )
    product.refresh_from_db()
    return product


def make_material(kind: str, *, name: str, pack_size: str, price_kop: int, weight: str,
                  unit: str = Product.Unit.BAG) -> Product:
    product = ProductFactory.create(kind=kind, unit=unit, name=name, price_kop=price_kop,
                             weight_kg=Decimal(weight), stock_qty=Decimal("1000"))
    MaterialSpec.objects.create(product=product, pack_size=Decimal(pack_size),
                                pack_unit=MaterialSpec.PackUnit.KG)
    return product


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def mocked_http():
    """Будь-який незамоканий HTTP-запит у тестах падає. Telegram відповідає успіхом."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.POST, TELEGRAM_URL, json={"ok": True})
        rsps.add(responses.POST, LOGIN_BOT_URL, json={"ok": True})
        yield rsps


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def run_on_commit(django_capture_on_commit_callbacks):
    """Виконує колбеки on_commit (події) у межах тестової транзакції."""
    def runner():
        return django_capture_on_commit_callbacks(execute=True)
    return runner


@pytest.fixture
def calc_settings_dict() -> dict:
    return json.loads((CALC_CASES / "settings.json").read_text())


@pytest.fixture
def published_settings(db, calc_settings_dict) -> CalcSettings:
    """Опубліковані налаштування, що відповідають calc-cases/settings.json."""
    data = calc_settings_dict
    materials = {
        kind: make_material(kind, name=item["name"], pack_size=item["pack_size"],
                            price_kop=item["price_kop"], weight=item["pack_weight_kg"])
        for kind, item in data["materials"].items()
    }
    for surface, rates in data["labor_kop_per_m2"].items():
        for size_class, price in rates.items():
            LaborRate.objects.create(surface=surface, size_class=size_class,
                                     price_kop_per_m2=price)
    return CalcSettings.objects.create(
        status=CalcSettings.Status.PUBLISHED,
        waste_by_layout=data["waste_by_layout"],
        glue_kg_per_m2=data["glue_kg_per_m2"],
        grout_density=Decimal(data["grout_density"]),
        primer_l_per_m2=Decimal(data["primer_l_per_m2"]),
        waterproofing_kg_per_m2=Decimal(data["waterproofing_kg_per_m2"]),
        glue_product=materials["glue"],
        grout_product=materials["grout"],
        primer_product=materials["primer"],
        waterproofing_product=materials["waterproofing"],
    )


@pytest.fixture
def tile(db) -> Product:
    return make_tile(name="Marble Grey 60×60")


@pytest.fixture
def customer_api(db):
    """Повертає (клієнт API з токеном, клієнт). Параметр master робить клієнта майстром."""
    from apps.customers import services as customer_services
    from apps.customers.models import Customer

    def make(phone: str = "+380671112233", *, master: bool = False):
        customer = Customer.objects.create(phone=phone, name="Тест", is_master=master)
        result = customer_services.login(customer)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {result.token}")
        return client, customer

    return make
