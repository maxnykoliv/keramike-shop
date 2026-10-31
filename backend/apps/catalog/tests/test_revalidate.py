import json

import pytest
import responses

from conftest import make_tile

pytestmark = pytest.mark.django_db
REVALIDATE_URL = "http://localhost:3000/api/revalidate"


def revalidate_calls(mocked_http) -> list:
    return [c for c in mocked_http.calls if c.request.url == REVALIDATE_URL]


def test_catalog_change_revalidates_site_once(settings, mocked_http, run_on_commit):
    settings.SITE_URL = "http://localhost:3000"
    settings.REVALIDATE_SECRET = "reval-secret"
    mocked_http.add(responses.POST, REVALIDATE_URL, json={"revalidated": "catalog"})
    with run_on_commit():
        make_tile(name="Перша")
        make_tile(name="Друга")
    calls = revalidate_calls(mocked_http)
    assert len(calls) == 1
    assert calls[0].request.headers["X-Revalidate-Secret"] == "reval-secret"
    assert json.loads(calls[0].request.body) == {"tag": "catalog"}


def test_no_secret_no_request(mocked_http, run_on_commit):
    with run_on_commit():
        make_tile()
    assert revalidate_calls(mocked_http) == []
