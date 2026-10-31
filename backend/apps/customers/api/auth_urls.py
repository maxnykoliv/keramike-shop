from django.urls import path

from apps.customers.api import views

urlpatterns = [
    path("methods", views.AuthMethodsView.as_view(), name="auth-methods"),
    path("telegram/start", views.TelegramStartView.as_view(), name="auth-telegram-start"),
    path("telegram/poll", views.TelegramPollView.as_view(), name="auth-telegram-poll"),
    path("telegram/webhook", views.TelegramWebhookView.as_view(), name="auth-telegram-webhook"),
    path("code/request", views.CodeRequestView.as_view(), name="auth-code-request"),
    path("code/verify", views.CodeVerifyView.as_view(), name="auth-code-verify"),
    path("logout", views.LogoutView.as_view(), name="auth-logout"),
    path("logout-all", views.LogoutAllView.as_view(), name="auth-logout-all"),
]
