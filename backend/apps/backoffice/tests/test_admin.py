"""Адмінка: сторінки відкриваються, права ролей працюють, кнопки змінюють статус."""

import pytest
from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.urls import reverse

from apps.calc import services as calc_services
from apps.cart import services as cart_services
from apps.core.roles import MANAGER_GROUP
from apps.orders import services as order_services
from apps.orders.models import Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_superuser("owner@example.com", "pass")


@pytest.fixture
def manager(django_user_model):
    call_command("setup_roles", verbosity=0)
    user = django_user_model.objects.create_user("manager@example.com", "pass")
    user.groups.add(Group.objects.get(name=MANAGER_GROUP))
    return user


@pytest.fixture
def order(tile):
    return order_services.create_order(
        customer=order_services.Customer(name="Іван", phone="+380671234567"),
        delivery_method="pickup", delivery={}, payment_method="cod",
        lines=order_services.build_lines([order_services.LineRequest(tile.id, 2)]),
        delivery_kop=0,
    )


def test_every_changelist_and_add_page_opens(client, owner, published_settings, order):
    client.force_login(owner)
    assert client.get(reverse("admin:index")).status_code == 200
    for model, model_admin in admin.site._registry.items():
        opts = model._meta
        url = reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
        response = client.get(url)
        assert response.status_code == 200, f"{url}: {response.status_code}"
        if model_admin.has_add_permission(type("R", (), {"user": owner})()):
            add = client.get(reverse(f"admin:{opts.app_label}_{opts.model_name}_add"))
            assert add.status_code == 200, f"add {opts.label}: {add.status_code}"


def test_change_pages_open(client, owner, published_settings, order, tile):
    client.force_login(owner)
    for name, pk in [("orders_order", order.pk), ("catalog_product", tile.pk),
                     ("calc_calcsettings", published_settings.pk)]:
        response = client.get(reverse(f"admin:{name}_change", args=[pk]))
        assert response.status_code == 200, name


def test_order_status_buttons(client, owner, order):
    client.force_login(owner)
    page = client.get(reverse("admin:orders_order_change", args=[order.pk])).content.decode()
    assert "Підтвердити" in page
    assert "Відправлено" not in page

    response = client.get(reverse("admin:orders_order_to_confirmed", args=[order.pk]))
    assert response.status_code == 302
    order.refresh_from_db()
    assert order.status == "confirmed"


def test_manager_cannot_change_price(client, manager, tile):
    client.force_login(manager)
    url = reverse("admin:catalog_product_change", args=[tile.pk])
    page = client.get(url)
    assert page.status_code == 200
    assert 'name="price_kop"' not in page.content.decode()


def test_manager_cannot_open_calc_settings_or_users(client, manager, published_settings):
    client.force_login(manager)
    assert client.get(reverse("admin:calc_calcsettings_changelist")).status_code == 403
    assert client.get(reverse("admin:accounts_user_changelist")).status_code == 403


def test_publish_settings_button(client, owner, published_settings):
    client.force_login(owner)
    draft = calc_services.clone_as_draft(published_settings)
    response = client.get(reverse("admin:calc_calcsettings_publish", args=[draft.pk]))
    assert response.status_code == 302
    draft.refresh_from_db()
    assert draft.status == "published"


def test_dashboard_shows_stats(client, owner, tile):
    cart = cart_services.create_cart()
    cart_services.add_item(cart, tile.id, 1)
    client.force_login(owner)
    page = client.get(reverse("admin:index")).content.decode()
    assert "Кошторисів" in page
    assert Order.objects.count() == 0
