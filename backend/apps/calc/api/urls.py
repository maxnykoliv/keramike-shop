from django.urls import path

from apps.calc.api import views

urlpatterns = [
    path("config", views.ConfigView.as_view(), name="calc-config"),
    path("estimate", views.EstimateView.as_view(), name="calc-estimate"),
    path("estimates", views.EstimateCreateView.as_view(), name="calc-estimates"),
    path("estimates/<str:code>", views.EstimateDetailView.as_view(), name="calc-estimate-detail"),
    path("estimates/<str:code>/pdf", views.EstimatePdfView.as_view(), name="calc-estimate-pdf"),
]
