from django.urls import path

from apps.leads.api import views

urlpatterns = [path("", views.LeadCreateView.as_view(), name="lead-create")]
