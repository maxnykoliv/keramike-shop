"""Чистий рушій калькулятора. Не імпортує Django — це перевіряє import-linter."""

from apps.calc.engine.core import calculate
from apps.calc.engine.errors import CalcValidationError
from apps.calc.engine.serialization import (
    input_from_dict,
    result_to_dict,
    settings_from_dict,
    settings_to_dict,
)

__all__ = [
    "CalcValidationError",
    "calculate",
    "input_from_dict",
    "result_to_dict",
    "settings_from_dict",
    "settings_to_dict",
]
