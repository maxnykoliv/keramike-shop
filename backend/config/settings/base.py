"""Спільні налаштування. Усе, що відрізняється між середовищами, читається зі змінних середовища."""

from datetime import timedelta
from pathlib import Path

import environ
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env", overwrite=False)

SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    # Unfold має йти перед django.contrib.admin.
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.import_export",
    "unfold.contrib.simple_history",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Сторонні пакети
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "import_export",
    "simple_history",
    "axes",
    "storages",
    # Застосунки проєкту, від основи до точок входу
    "apps.core",
    "apps.accounts",
    "apps.customers",
    "apps.catalog",
    "apps.calc",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.delivery",
    "apps.leads",
    "apps.checkout",
    "apps.notifications",
    "apps.backoffice",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "apps.core.middleware.RequestIdMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    # django-axes має бути останнім.
    "axes.middleware.AxesMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": "keramike",
    }
}

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

# Блокування входу після 5 невдалих спроб на 15 хвилин.
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_RESET_ON_SUCCESS = True
AXES_CLIENT_IP_CALLABLE = "apps.core.security.client_ip"

# IP клієнта (apps.core.security.client_ip). Сайт передає його із секретом BFF_SHARED_SECRET,
# який має збігатися зі змінною BFF_SECRET на Vercel. TRUSTED_PROXY_COUNT — скільки проксі
# перед Django дописують X-Forwarded-For: 0 локально, 1 на Railway.
BFF_SHARED_SECRET = env("BFF_SHARED_SECRET", default="")
TRUSTED_PROXY_COUNT = env.int("TRUSTED_PROXY_COUNT", default=0)

LANGUAGE_CODE = "uk"
TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
if AWS_STORAGE_BUCKET_NAME:
    # Cloudflare R2 через S3-сумісний API.
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL")
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    DEFAULT_FILE_STORAGE_BACKEND = "storages.backends.s3.S3Storage"
else:
    DEFAULT_FILE_STORAGE_BACKEND = "django.core.files.storage.FileSystemStorage"

STORAGES = {
    "default": {"BACKEND": DEFAULT_FILE_STORAGE_BACKEND},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
CORS_ALLOW_HEADERS = (
    "accept",
    "content-type",
    "idempotency-key",
    "x-request-id",
)

REST_FRAMEWORK = {
    # Клієнти — токен сесії в заголовку Authorization. Персонал — сесія Django admin.
    "DEFAULT_AUTHENTICATION_CLASSES": ["apps.customers.authentication.CustomerTokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.PagePagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": ["apps.core.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "forms": env("THROTTLE_FORMS", default="20/hour"),
        "estimates": env("THROTTLE_ESTIMATES", default="120/hour"),
        "auth": env("THROTTLE_AUTH", default="30/hour"),
    },
    "COERCE_DECIMAL_TO_STRING": True,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Keramike API",
    "DESCRIPTION": "Публічне API магазину кераміки: каталог, калькулятор, кошик, замовлення.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "ProductKindEnum": "apps.catalog.models.Product.Kind",
        "DeliveryMethodEnum": "apps.orders.state.DeliveryMethod",
        "PaymentMethodEnum": "apps.orders.state.PaymentMethod",
        "OrderStatusEnum": "apps.orders.state.OrderStatus",
        "PaymentStatusEnum": "apps.orders.state.PaymentStatus",
        "AddressDeliveryMethodEnum": "apps.customers.models.CustomerAddress.Method",
    },
}

# Celery: дві черги, щоб важкі задачі не затримували сповіщення.
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = None
CELERY_TASK_DEFAULT_QUEUE = "default"
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_ROUTES = {
    "apps.calc.tasks.render_estimate_pdf": {"queue": "heavy"},
    "apps.catalog.tasks.process_image": {"queue": "heavy"},
    "apps.core.tasks.backup_database": {"queue": "heavy"},
}
CELERY_BEAT_SCHEDULE = {
    "delivery-sync-parcel-statuses": {
        "task": "apps.delivery.tasks.sync_parcel_statuses",
        "schedule": crontab(minute=0),
    },
    "orders-remind-unconfirmed": {
        "task": "apps.orders.tasks.remind_unconfirmed",
        "schedule": crontab(minute="*/15"),
    },
    "cart-cleanup-expired": {
        "task": "apps.cart.tasks.cleanup_expired",
        "schedule": crontab(hour=3, minute=0),
    },
    "core-backup-database": {
        "task": "apps.core.tasks.backup_database",
        "schedule": crontab(hour=3, minute=30),
    },
}

# Інтеграції
SITE_URL = env("SITE_URL", default="http://localhost:3000")
# Той самий рядок, що й REVALIDATE_SECRET на Vercel. Порожньо — сайт оновлює каталог за 5 хвилин.
REVALIDATE_SECRET = env("REVALIDATE_SECRET", default="")
API_URL = env("API_URL", default="http://localhost:8000")

PAYMENT_PROVIDER = env("PAYMENT_PROVIDER", default="fake")
PAYMENT_PUBLIC_KEY = env("PAYMENT_PUBLIC_KEY", default="")
PAYMENT_PRIVATE_KEY = env("PAYMENT_PRIVATE_KEY", default="")

NOVA_POSHTA_API_KEY = env("NOVA_POSHTA_API_KEY", default="")
NOVA_POSHTA_API_URL = "https://api.novaposhta.ua/v2.0/json/"

# Бот входу для клієнтів — окремий від бота сповіщень менеджеру.
TELEGRAM_LOGIN_BOT_TOKEN = env("TELEGRAM_LOGIN_BOT_TOKEN", default="")
TELEGRAM_LOGIN_BOT_USERNAME = env("TELEGRAM_LOGIN_BOT_USERNAME", default="")
TELEGRAM_WEBHOOK_SECRET = env("TELEGRAM_WEBHOOK_SECRET", default="")
# Канали одноразових кодів: console (розробка), згодом viber, sms.
AUTH_CODE_CHANNELS = env.list("AUTH_CODE_CHANNELS", default=[])
CUSTOMER_SESSION_DAYS = env.int("CUSTOMER_SESSION_DAYS", default=60)
# Лише для розробки й e2e: канал console дописує коди в цей файл.
AUTH_CONSOLE_OUTBOX_FILE = env("AUTH_CONSOLE_OUTBOX_FILE", default="")

TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", default="")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID", default="")

EMAIL_CONFIG = env.email_url("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Keramike <noreply@localhost>")

TURNSTILE_SECRET_KEY = env("TURNSTILE_SECRET_KEY", default="")

BACKUP_ENABLED = env.bool("BACKUP_ENABLED", default=False)

UNFOLD = {
    "SITE_TITLE": "Keramike",
    "SITE_HEADER": "Keramike — адмінка",
    "SITE_SYMBOL": "grid_view",
    "SHOW_HISTORY": True,
    "DASHBOARD_CALLBACK": "apps.backoffice.dashboard.dashboard_callback",
}

from apps.core.logging import configure_logging  # noqa: E402

LOG_JSON = env.bool("LOG_JSON", default=not DEBUG)
LOGGING = configure_logging(json=LOG_JSON, level=env("LOG_LEVEL", default="INFO"))
