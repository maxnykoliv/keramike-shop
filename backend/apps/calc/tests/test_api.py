import pytest

from apps.calc import services
from apps.calc.models import CalcSettings, Estimate
from apps.core.exceptions import InvalidTransition

pytestmark = pytest.mark.django_db


def floor_payload(product_id: int, **include) -> dict:
    return {
        "room": "bathroom",
        "surfaces": [{"kind": "floor", "product_id": product_id, "length_m": "2.0",
                      "width_m": "1.7", "layout": "straight"}],
        "include": {"glue": True, "grout": True, "primer": False, "waterproofing": False,
                    "labor": False, **include},
    }


def test_config_returns_engine_settings(api, published_settings, calc_settings_dict):
    response = api.get("/api/v1/calc/config")
    assert response.status_code == 200
    data = response.json()
    assert data["waste_by_layout"] == calc_settings_dict["waste_by_layout"]
    assert data["labor_kop_per_m2"] == calc_settings_dict["labor_kop_per_m2"]
    assert set(data["materials"]) == {"glue", "grout", "primer", "waterproofing"}


def test_config_without_published_settings(api, db):
    response = api.get("/api/v1/calc/config")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_estimate_with_catalog_tile_matches_example(api, published_settings, tile):
    response = api.post("/api/v1/calc/estimate", floor_payload(tile.id), format="json")
    assert response.status_code == 200, response.json()
    data = response.json()
    assert data["surfaces"][0]["packs"] == 3
    assert data["total_kop"] == 343800
    tile_line = data["lines"][0]
    assert tile_line["product_id"] == tile.id
    assert tile_line["name"] == tile.name


def test_estimate_manual_tile(api, published_settings):
    payload = {
        "room": "kitchen",
        "surfaces": [{"kind": "floor", "area_m2": "10",
                      "tile": {"width_mm": 300, "height_mm": 300, "price_kop_per_m2": 40000,
                               "m2_per_pack": "1.08"}}],
        "include": {"glue": False, "grout": False, "primer": False, "waterproofing": False,
                    "labor": False},
    }
    response = api.post("/api/v1/calc/estimate", payload, format="json")
    assert response.status_code == 200
    assert response.json()["surfaces"][0]["packs"] == 11  # 11 м² / 1,08


def test_validation_error_format(api, published_settings, tile):
    payload = floor_payload(tile.id)
    del payload["surfaces"][0]["width_m"]
    response = api.post("/api/v1/calc/estimate", payload, format="json")
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


def test_engine_error_has_field(api, published_settings, tile):
    payload = {
        "room": "hallway",
        "surfaces": [{"kind": "walls", "product_id": tile.id, "length_m": "1", "width_m": "1",
                      "height_m": "1", "openings": [{"width_m": "3", "height_m": "2"}]}],
    }
    response = api.post("/api/v1/calc/estimate", payload, format="json")
    assert response.status_code == 400
    assert response.json() == {"code": "openings_exceed_area", "field": "surfaces[0].openings",
                               "message": "Прорізи не можуть бути більшими за площу стін"}


def test_save_and_open_estimate(api, published_settings, tile):
    response = api.post("/api/v1/calc/estimates", floor_payload(tile.id), format="json")
    assert response.status_code == 201
    code = response.json()["code"]
    assert len(code) == 8

    opened = api.get(f"/api/v1/calc/estimates/{code.lower()}").json()
    assert opened["changed"] is False
    assert opened["result"]["total_kop"] == 343800

    tile.price_kop = 70000
    tile.save()
    reopened = api.get(f"/api/v1/calc/estimates/{code}").json()
    assert reopened["result"]["total_kop"] == 343800
    assert reopened["current"]["total_kop"] == 3 * 144 * 700 + 45000 + 18000
    assert reopened["changed"] is True


def test_pdf_without_weasyprint_is_rendering(api, published_settings, tile):
    estimate = services.save_estimate(floor_payload(tile.id))
    response = api.get(f"/api/v1/calc/estimates/{estimate.public_code}/pdf")
    assert response.status_code in (200, 202)


def test_hidden_tile_rejected(api, published_settings, tile):
    tile.status = tile.Status.HIDDEN
    tile.save()
    response = api.post("/api/v1/calc/estimate", floor_payload(tile.id), format="json")
    assert response.status_code == 400
    assert response.json()["field"] == "surfaces[0].product_id"


def test_publish_flow(published_settings, django_user_model):
    owner = django_user_model.objects.create_superuser("owner@example.com", "pass")
    draft = services.clone_as_draft(published_settings)
    assert draft.status == CalcSettings.Status.DRAFT
    assert draft.version == published_settings.version + 1

    draft.waste_by_layout = {**draft.waste_by_layout, "straight": "0.05"}
    draft.save()
    assert services.preview(draft)["surfaces"][0]["area_with_waste_m2"] == "3.57"

    services.publish_settings(draft, owner)
    published_settings.refresh_from_db()
    assert published_settings.status == CalcSettings.Status.ARCHIVED
    assert CalcSettings.objects.get(status=CalcSettings.Status.PUBLISHED) == draft

    with pytest.raises(InvalidTransition):
        services.publish_settings(draft, owner)


def test_estimate_keeps_settings_version(published_settings, tile):
    estimate = services.save_estimate(floor_payload(tile.id))
    assert Estimate.objects.get(pk=estimate.pk).settings == published_settings
    assert estimate.result["settings_version"] == published_settings.version
