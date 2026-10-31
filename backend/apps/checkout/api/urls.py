from django.urls import path

from apps.checkout.api import views

urlpatterns = [
    path("", views.CheckoutView.as_view(), name="checkout"),
    path("<str:token>/pay", views.RetryPaymentView.as_view(), name="order-pay"),
]
