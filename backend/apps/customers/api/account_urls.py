from django.urls import path

from apps.customers.api import views

urlpatterns = [
    path("me", views.MeView.as_view(), name="account-me"),
    path("addresses", views.AddressListView.as_view(), name="account-addresses"),
    path("addresses/<int:pk>", views.AddressDetailView.as_view(), name="account-address"),
]
