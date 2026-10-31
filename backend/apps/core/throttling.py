from rest_framework.throttling import ScopedRateThrottle as BaseScopedRateThrottle


class ScopedRateThrottle(BaseScopedRateThrottle):
    """Ліміти за справжнім IP клієнта, а не за X-Forwarded-For, який легко підробити."""

    def get_ident(self, request) -> str:
        # Імпорт тут: DRF завантажує цей клас під час імпорту apps.core.exceptions,
        # від якого залежить apps.core.security.
        from apps.core.security import client_ip

        return client_ip(request) or "unknown"
