from django.urls import path

from apps.payments.api import views

urlpatterns = [
    path("webhook/<str:provider>", views.WebhookView.as_view(), name="payment-webhook"),
]
