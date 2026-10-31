from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.views import health

api_v1: list[URLPattern | URLResolver] = [
    path("catalog/", include("apps.catalog.api.urls")),
    path("calc/", include("apps.calc.api.urls")),
    path("carts/", include("apps.cart.api.urls")),
    path("orders/", include("apps.checkout.api.urls")),
    path("orders/", include("apps.orders.api.urls")),
    path("payments/", include("apps.payments.api.urls")),
    path("delivery/", include("apps.delivery.api.urls")),
    path("leads/", include("apps.leads.api.urls")),
    path("auth/", include("apps.customers.api.auth_urls")),
    path("account/", include("apps.customers.api.account_urls")),
    path("account/", include("apps.orders.api.account_urls")),
    path("account/", include("apps.calc.api.account_urls")),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

urlpatterns = [
    path("health", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
