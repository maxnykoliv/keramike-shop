from django.urls import path

from apps.calc.api.account_views import AccountEstimatesView

urlpatterns = [path("estimates", AccountEstimatesView.as_view(), name="account-estimates")]
