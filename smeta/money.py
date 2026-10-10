"""Decimal money helpers. Estimates are summed in kopecks, never in floats."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CENT = Decimal("0.01")
ZERO = Decimal("0")
ONE = Decimal("1")


def dec(value, default: Decimal = ZERO) -> Decimal:
    """Parse anything a user or a CSV can contain: '1 234,56', '1234.56', 12, 12.5, ''."""
    if isinstance(value, Decimal):
        return value
    if value is None:
        return default
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    text = str(value).strip().replace(" ", "").replace(" ", "").replace(",", ".")
    if not text or text == "-":
        return default
    try:
        return Decimal(text)
    except InvalidOperation:
        return default


def money(value) -> Decimal:
    """Round to kopecks, half-up (as every Russian estimate form does)."""
    return dec(value).quantize(CENT, rounding=ROUND_HALF_UP)


def pct(value) -> Decimal:
    """Percent -> multiplier: 20 -> 0.2."""
    return dec(value) / Decimal(100)


def rub(value) -> str:
    """1234567.891 -> '1 234 567,89'."""
    return f"{money(value):,.2f}".replace(",", " ").replace(".", ",")


def qty_str(value) -> str:
    """Quantity without trailing zeros: 12.500 -> '12,5', 3 -> '3'."""
    q = dec(value).normalize()
    text = format(q, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",") or "0"
