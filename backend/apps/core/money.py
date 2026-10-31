"""Money: integer kopiykas in the DB, Decimal in calculations, never float."""

from decimal import ROUND_HALF_UP, Decimal

ONE = Decimal("1")
HUNDRED = Decimal("100")


def round_kop(value: Decimal) -> int:
    """Rounds an amount in kopiykas to an integer with ROUND_HALF_UP."""
    return int(value.quantize(ONE, rounding=ROUND_HALF_UP))


def kop_to_uah(kop: int) -> Decimal:
    return (Decimal(kop) / HUNDRED).quantize(Decimal("0.01"))


def uah_to_kop(uah: Decimal | str) -> int:
    return round_kop(Decimal(uah) * HUNDRED)


def format_uah(kop: int) -> str:
    """Formats 280800 as "2 808,00 грн"."""
    value = kop_to_uah(kop)
    whole, frac = f"{value:.2f}".split(".")
    sign = "-" if whole.startswith("-") else ""
    whole = whole.lstrip("-")
    groups: list[str] = []
    while whole:
        groups.insert(0, whole[-3:])
        whole = whole[:-3]
    return f"{sign}{' '.join(groups)},{frac} грн"
