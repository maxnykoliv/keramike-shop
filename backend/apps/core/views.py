from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def health(request):
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"
    try:
        cache.set("health", "1", 5)
        checks["cache"] = "ok" if cache.get("health") == "1" else "error"
    except Exception:
        checks["cache"] = "error"
    healthy = all(value == "ok" for value in checks.values())
    return JsonResponse({"status": "ok" if healthy else "error", **checks},
                        status=200 if healthy else 503)
