from django.urls import path

from apps.orders.api.account_views import AccountOrdersView

urlpatterns = [path("orders", AccountOrdersView.as_view(), name="account-orders")]
