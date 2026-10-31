from apps.core.logging import configure_logging

from .base import *  # noqa: F403
from .base import env

DEBUG = True
ALLOWED_HOSTS = ["*"]
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
STORAGES["staticfiles"] = {  # noqa: F405
    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
}

# Without Redis (e.g. without Docker): in-memory cache, Celery tasks run synchronously.
if not env("REDIS_URL", default=""):
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = False

LOGGING = configure_logging(json=env.bool("LOG_JSON", default=False),
                            level=env("LOG_LEVEL", default="INFO"))
