"""Free text -> draft estimate lines.

People type what they would say out loud:

    Штукатурка стен 120 м2
    стяжка пола 85 м2 по 700
    плитка на пол 2,7х4,2 м2 х 1500
    - розетки 24 точки
    мат: керамогранит 22 м2 1200 р/м2
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

from .model import MATERIAL, WORK
from .money import ONE, dec
from .units import UNIT_PATTERN, norm_unit

NUM = r"\d{1,3}(?:[  ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?"
_UNIT = f"(?:{UNIT_PATTERN})"
_CURRENCY = r"(?:(?:рублей|рубля|руб|₽|р)\.?(?!\w))"

_BULLET = re.compile(r"^\s*(?:\d{1,2}\s*[).]|[-—–*•·+])\s*")
_MATERIAL_PREFIX = re.compile(r"^\s*(?:мат|материал|материалы)\s*[.:\-]\s*", re.I)
_MATERIAL_MARK = re.compile(r"\(\s*материал\w*\s*\)", re.I)

# Price: "по 700", "цена 700", "700 р/м2", "х 1500", "= 700"
_PRICE_PATTERNS = (
    re.compile(rf"(?:по|цена|прайс|стоимость|расценка|ставка)\s*[:=]?\s*({NUM})\s*{_CURRENCY}?", re.I),
    re.compile(rf"(?<![\w,.])({NUM})\s*{_CURRENCY}\s*(?:/|за\s*)\s*{_UNIT}", re.I),
    # "х 1500" only at the end of the line - inside a name it is a size: "кабель 3х2.5"
    re.compile(rf"(?:[xх*×])\s*({NUM})\s*{_CURRENCY}?\s*$", re.I),
    re.compile(rf"(?<![\w,.])({NUM})\s*{_CURRENCY}", re.I),
)
# Dimensions: "2,7х4,2 м2", "3*4 м"
_DIMENSIONS = re.compile(rf"(?<![\w,.])({NUM})\s*[xх*×]\s*({NUM})\s*({_UNIT})\b", re.I)
# Quantity: "120 м2", "м2 120" is not accepted - people write the number first
_QTY = re.compile(rf"(?<![\w,.])({NUM})\s*({_UNIT})\b", re.I)
_BARE_QTY = re.compile(rf"(?:^|\s)({NUM})(?:\s|$)")
# A number left at the very end of a line is the unit price: "керамогранит 22 м2 1550".
_TRAILING_NUM = re.compile(rf"(?<![\w,.])({NUM})\s*$")


@dataclass
class DraftLine:
    """One parsed line, before it meets the rate catalog."""

    raw: str
    name: str
    qty: Decimal = ONE
    unit: str = "шт"
    price: Decimal | None = None
    kind: str = WORK
    qty_guessed: bool = False

    @property
    def has_price(self) -> bool:
        return self.price is not None and self.price > 0


def _num(text: str) -> Decimal:
    return dec((text or "").replace(" ", "").replace(" ", ""))


def _cut(text: str, span: tuple[int, int]) -> str:
    return f"{text[: span[0]]} {text[span[1]:]}"


def _clean_name(text: str) -> str:
    text = _MATERIAL_MARK.sub(" ", text)
    text = re.sub(rf"\b{_CURRENCY}\b", " ", text, flags=re.I)
    text = re.sub(r"[;,]+\s*$", "", text)
    text = re.sub(r"^[\s\-—–:;.]+|[\s\-—–:;.]+$", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def parse_line(raw: str) -> DraftLine | None:
    """Parse one line. Returns None if nothing usable is left (e.g. a bare number)."""
    text = (raw or "").strip()
    if not text:
        return None
    text = _BULLET.sub("", text)
    kind = WORK
    if _MATERIAL_PREFIX.search(text) or _MATERIAL_MARK.search(text):
        kind = MATERIAL
        text = _MATERIAL_PREFIX.sub("", text)

    qty: Decimal | None = None
    unit = ""
    dims = _DIMENSIONS.search(text)
    if dims:
        qty = _num(dims.group(1)) * _num(dims.group(2))
        unit = norm_unit(dims.group(3))
        text = _cut(text, dims.span())

    price: Decimal | None = None
    for pattern in _PRICE_PATTERNS:
        match = pattern.search(text)
        if match:
            price = _num(match.group(1))
            text = _cut(text, match.span())
            break

    if qty is None:
        # The LAST quantity wins: in "штукатурка гипсовая 30 кг 170 шт" the 30 kg belongs
        # to the product name and 170 pieces is what we are buying.
        found = list(_QTY.finditer(text))
        if found:
            match = found[-1]
            qty = _num(match.group(1))
            unit = norm_unit(match.group(2))
            text = _cut(text, match.span())

    if price is None:
        match = _TRAILING_NUM.search(text)
        if match:
            price = _num(match.group(1))
            text = _cut(text, match.span())

    guessed = False
    if qty is None:
        match = _BARE_QTY.search(text)
        if match:
            qty = _num(match.group(1))
            text = _cut(text, match.span())
        else:
            qty, guessed = ONE, True

    name = _clean_name(text)
    if not name:
        return None
    return DraftLine(
        raw=raw.strip(),
        name=name,
        qty=qty if qty is not None else ONE,
        unit=unit or "шт",
        price=price,
        kind=kind,
        qty_guessed=guessed,
    )


def parse_text(text: str) -> list[DraftLine]:
    """Split a message into lines (newlines and ';') and parse each one."""
    out: list[DraftLine] = []
    for chunk in re.split(r"[\n;]+", text or ""):
        line = parse_line(chunk)
        if line:
            out.append(line)
    return out
