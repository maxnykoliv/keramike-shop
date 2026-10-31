"""Нормалізація телефонів до E.164. За телефоном пов'язуються клієнт, замовлення і Telegram."""

import re

DIGITS = re.compile(r"\D")


class InvalidPhone(ValueError):
    pass


def normalize_phone(value: str) -> str:
    """'+380 (67) 123-45-67', '0671234567', '380671234567' → '+380671234567'."""
    raw = (value or "").strip()
    digits = DIGITS.sub("", raw)
    if len(digits) == 10 and digits.startswith("0"):
        digits = "38" + digits
    elif len(digits) == 9:
        digits = "380" + digits
    if digits.startswith("380") and len(digits) == 12:
        return "+" + digits
    if raw.startswith("+") and 10 <= len(digits) <= 15:
        return "+" + digits
    raise InvalidPhone("Некоректний номер телефону")
