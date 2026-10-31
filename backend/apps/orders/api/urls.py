from django.urls import path

from apps.orders.api import views

urlpatterns = [
    path("<str:token>", views.OrderStatusView.as_view(), name="order-status"),
]
