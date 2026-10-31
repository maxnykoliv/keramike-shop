from django.urls import path

from apps.catalog.api import views

urlpatterns = [
    path("categories", views.CategoryTreeView.as_view(), name="catalog-categories"),
    path("products", views.ProductListView.as_view(), name="catalog-products"),
    path("products/<slug:slug>", views.ProductDetailView.as_view(), name="catalog-product"),
    path("facets", views.FacetsView.as_view(), name="catalog-facets"),
    path("search", views.SearchView.as_view(), name="catalog-search"),
    path("prices", views.PersonalPricesView.as_view(), name="catalog-prices"),
]
