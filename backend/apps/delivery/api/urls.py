from django.urls import path

from apps.delivery.api import views

urlpatterns = [
    path("np/cities", views.CitiesView.as_view(), name="np-cities"),
    path("np/warehouses", views.WarehousesView.as_view(), name="np-warehouses"),
    path("quote", views.QuoteView.as_view(), name="delivery-quote"),
]
