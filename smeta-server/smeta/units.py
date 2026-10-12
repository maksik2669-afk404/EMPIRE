"""Units of measure: user spelling -> canonical form, and '100 м2' -> (100, 'м2')."""
from __future__ import annotations

import re
from decimal import Decimal

from .money import ONE, dec

# canonical -> everything people actually type
_ALIASES: dict[str, tuple[str, ...]] = {
    "м2": ("м2", "м²", "кв.м", "кв. м", "квм", "кв.метр", "m2", "метр2"),
    "м3": ("м3", "м³", "куб.м", "куб. м", "кубм", "куб", "m3"),
    "м": ("м", "пог.м", "пог. м", "п.м", "пм", "мп", "м.п", "метр", "метров", "погм"),
    "шт": ("шт", "шт.", "штук", "штука", "штуки", "ед", "ед.", "единица"),
    "т": ("т", "тн", "тонн", "тонна", "тонны"),
    "кг": ("кг", "килограмм", "килограммов"),
    "л": ("л", "литр", "литров"),
    "компл": ("компл", "комплект", "комплектов", "к-т", "набор"),
    "м/ч": ("м/ч", "маш.-ч", "маш-ч", "машч"),
    "чел.-ч": ("чел.-ч", "чел-ч", "челч", "час", "часов", "ч"),
    "точка": ("точка", "точек", "точки"),
    "мес": ("мес", "месяц", "месяцев"),
    "%": ("%", "процент", "процентов"),
}
_LOOKUP: dict[str, str] = {}
for _canon, _forms in _ALIASES.items():
    _LOOKUP[_canon] = _canon
    for _form in _forms:
        _LOOKUP[_form.replace(" ", "").replace(".", "")] = _canon

def _form_regex(form: str) -> str:
    """'кв.м' -> 'кв[.\\s]?м', so 'кв.м', 'кв. м' and 'кв м' all match."""
    return "".join("[.\\s]?" if ch in ". " else re.escape(ch) for ch in form)


UNIT_PATTERN = "|".join(
    _form_regex(f)
    for f in sorted({f for forms in _ALIASES.values() for f in forms}, key=len, reverse=True)
)


def norm_unit(text: str | None) -> str:
    """'кв. м' -> 'м2'. Unknown units are kept as typed (trimmed)."""
    if not text:
        return ""
    raw = str(text).strip().lower().replace(" ", " ")
    return _LOOKUP.get(raw.replace(" ", "").replace(".", ""), raw)


def parse_unit(text: str | None) -> tuple[Decimal, str]:
    """FER units come as '100 м2', '1000 м3', '10 т'. Return (factor, canonical unit)."""
    raw = (text or "").strip().lower().replace(" ", " ")
    match = re.match(r"^(\d+(?:[.,]\d+)?)\s*(.+)$", raw)
    if match:
        return dec(match.group(1)) or ONE, norm_unit(match.group(2))
    return ONE, norm_unit(raw)


def same_unit(a: str | None, b: str | None) -> bool:
    return norm_unit(a) == norm_unit(b)
