"""calc-cases golden tests. Vitest runs the same files against the TypeScript port."""

import json
from pathlib import Path

import pytest

from apps.calc import engine

ROOT = Path(__file__).resolve().parents[4] / "calc-cases"
SETTINGS = engine.settings_from_dict(json.loads((ROOT / "settings.json").read_text()))
CASES = sorted((ROOT / "cases").glob("*.json"))


def summarize(result: dict) -> dict:
    return {
        "surfaces": [{k: s[k] for k in ("area_m2", "area_with_waste_m2", "packs")}
                     for s in result["surfaces"]],
        "lines": [{k: line[k] for k in ("kind", "quantity", "quantity_base", "total_kop",
                                         "weight_kg")} for line in result["lines"]],
        "total_kop": result["total_kop"],
        "weight_kg": result["weight_kg"],
        "warnings": [w["code"] for w in result["warnings"]],
    }


def test_cases_exist():
    assert len(CASES) >= 5


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_golden_case(path: Path):
    case = json.loads(path.read_text())
    data = engine.input_from_dict(case["input"])
    if "expected_error" in case:
        with pytest.raises(engine.CalcValidationError) as exc:
            engine.calculate(data, SETTINGS)
        assert {"code": exc.value.code, "field": exc.value.field} == case["expected_error"]
        return
    result = engine.result_to_dict(engine.calculate(data, SETTINGS))
    assert summarize(result) == case["expected"]


def test_settings_roundtrip():
    assert engine.settings_from_dict(engine.settings_to_dict(SETTINGS)) == SETTINGS


def test_missing_material_gives_warning():
    settings = engine.settings_from_dict({**engine.settings_to_dict(SETTINGS), "materials": {}})
    case = json.loads((ROOT / "cases" / "01_bathroom_floor_example.json").read_text())
    result = engine.calculate(engine.input_from_dict(case["input"]), settings)
    assert [line.kind for line in result.lines] == ["tile"]
    assert "material_not_configured" in [w.code for w in result.warnings]


def test_unknown_pack_size_is_validation_error():
    data = engine.input_from_dict({
        "room": "other",
        "surfaces": [{"kind": "floor", "area_m2": "5",
                      "tile": {"width_mm": 300, "height_mm": 300, "price_kop_per_m2": 1}}],
    })
    with pytest.raises(engine.CalcValidationError) as exc:
        engine.calculate(data, SETTINGS)
    assert exc.value.code == "pack_unknown"
