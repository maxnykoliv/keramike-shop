import pytest
from django.test import RequestFactory

from apps.core.security import client_ip

rf = RequestFactory()


@pytest.fixture(autouse=True)
def _bff(settings):
    settings.BFF_SHARED_SECRET = "bff-secret"
    settings.TRUSTED_PROXY_COUNT = 1


def test_site_passes_client_ip_with_secret():
    request = rf.get("/", HTTP_X_BFF_SECRET="bff-secret", HTTP_X_CLIENT_IP="203.0.113.7",
                     HTTP_X_FORWARDED_FOR="198.51.100.1, 10.0.0.2")
    assert client_ip(request) == "203.0.113.7"


def test_client_ip_header_without_secret_is_ignored():
    request = rf.get("/", HTTP_X_BFF_SECRET="guess", HTTP_X_CLIENT_IP="1.1.1.1",
                     HTTP_X_FORWARDED_FOR="1.1.1.1, 198.51.100.9")
    assert client_ip(request) == "198.51.100.9"


def test_spoofed_forwarded_for_takes_address_added_by_proxy():
    request = rf.get("/", HTTP_X_FORWARDED_FOR="6.6.6.6, 7.7.7.7, 198.51.100.9")
    assert client_ip(request) == "198.51.100.9"


def test_invalid_values_fall_back_to_remote_addr(settings):
    request = rf.get("/", HTTP_X_BFF_SECRET="bff-secret", HTTP_X_CLIENT_IP="not-an-ip",
                     HTTP_X_FORWARDED_FOR="garbage", REMOTE_ADDR="10.0.0.5")
    assert client_ip(request) == "10.0.0.5"
    settings.TRUSTED_PROXY_COUNT = 0
    request = rf.get("/", HTTP_X_FORWARDED_FOR="6.6.6.6", REMOTE_ADDR="10.0.0.5")
    assert client_ip(request) == "10.0.0.5"


def test_throttle_counts_by_real_ip():
    from apps.core.throttling import ScopedRateThrottle

    request = rf.get("/", HTTP_X_FORWARDED_FOR="6.6.6.6, 198.51.100.9")
    assert ScopedRateThrottle().get_ident(request) == "198.51.100.9"
