from rest_framework.throttling import ScopedRateThrottle as BaseScopedRateThrottle


class ScopedRateThrottle(BaseScopedRateThrottle):
    """Rate limits by the real client IP rather than X-Forwarded-For, which is easy to spoof."""

    def get_ident(self, request) -> str:
        # Imported here: DRF loads this class while apps.core.exceptions is being imported,
        # and apps.core.security depends on that module.
        from apps.core.security import client_ip

        return client_ip(request) or "unknown"
