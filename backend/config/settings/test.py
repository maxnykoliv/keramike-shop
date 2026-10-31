import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DATABASE_URL", "postgres://keramike@127.0.0.1:5433/keramike")

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["*"]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
PAYMENT_PROVIDER = "fake"
PAYMENT_PRIVATE_KEY = "test-private-key"
TELEGRAM_BOT_TOKEN = "test-token"
TELEGRAM_CHAT_ID = "1"
NOVA_POSHTA_API_KEY = "test-np-key"
TURNSTILE_SECRET_KEY = ""
TELEGRAM_LOGIN_BOT_TOKEN = "login-token"
TELEGRAM_LOGIN_BOT_USERNAME = "keramike_login_bot"
TELEGRAM_WEBHOOK_SECRET = "hook-secret"
AUTH_CODE_CHANNELS = ["console"]
AXES_ENABLED = False
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_THROTTLE_CLASSES": [],
}
LOGGING = {"version": 1, "disable_existing_loggers": False}
MIDDLEWARE = [m for m in MIDDLEWARE if m != "whitenoise.middleware.WhiteNoiseMiddleware"]  # noqa: F405
