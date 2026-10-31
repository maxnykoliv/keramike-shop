from django.urls import path

from apps.cart.api import views

urlpatterns = [
    path("", views.CartCreateView.as_view(), name="cart-create"),
    path("<str:token>", views.CartDetailView.as_view(), name="cart-detail"),
    path("<str:token>/items", views.CartItemsView.as_view(), name="cart-items"),
    path("<str:token>/items/<int:item_id>", views.CartItemDetailView.as_view(),
         name="cart-item"),
    path("<str:token>/from-estimate/<str:code>", views.CartFromEstimateView.as_view(),
         name="cart-from-estimate"),
]
