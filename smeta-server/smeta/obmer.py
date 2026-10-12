"""Обмерный калькулятор: из размеров помещений — площади и длины для всех работ."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from decimal import Decimal

from .money import ZERO, dec, money, qty_str

DOOR_W, DOOR_H = Decimal("0.9"), Decimal("2.1")
WIN_W, WIN_H = Decimal("1.5"), Decimal("1.5")
_NUM = r"\d+(?:[.,]\d+)?"


@dataclass
class Room:
    name: str
    length: Decimal
    width: Decimal
    height: Decimal
    doors: int = 1
    windows: int = 1

    def __post_init__(self) -> None:
        self.length, self.width, self.height = dec(self.length), dec(self.width), dec(self.height)
        self.doors, self.windows = int(self.doors), int(self.windows)

    @property
    def floor(self) -> Decimal:
        return money(self.length * self.width)

    @property
    def perimeter(self) -> Decimal:
        return money(2 * (self.length + self.width))

    @property
    def openings(self) -> Decimal:
        return money(self.doors * DOOR_W * DOOR_H + self.windows * WIN_W * WIN_H)

    @property
    def walls(self) -> Decimal:
        return money(max(self.perimeter * self.height - self.openings, ZERO))

    @property
    def plinth(self) -> Decimal:
        return money(max(self.perimeter - self.doors * DOOR_W, ZERO))

    @property
    def slopes(self) -> Decimal:
        """Откосы окон: две стороны и верх."""
        return money(self.windows * (2 * WIN_H + WIN_W))

    def as_text(self) -> str:
        return (f"🏠 {self.name}: {qty_str(self.length)}×{qty_str(self.width)}, h {qty_str(self.height)} м, "
                f"дверей {self.doors}, окон {self.windows}\n"
                f"   пол {qty_str(self.floor)} м² · стены {qty_str(self.walls)} м² · периметр {qty_str(self.perimeter)} м")

    def to_dict(self) -> dict:
        return {k: (str(v) if isinstance(v, Decimal) else v) for k, v in asdict(self).items()}


def parse_room(text: str, default_name: str = "Помещение") -> Room:
    """'кухня 4,2х3,1 2,7 д1 о2', '4.2 3.1 2.7', '5x4x3 д2 о0'."""
    raw = (text or "").strip().lower()
    # «х» как знак умножения - только между числами, иначе испортим «кухня»
    raw = re.sub(r"(?<=\d)\s*[хx×*]\s*(?=\d)", " ", raw)
    doors = re.search(r"\bд(?:вер\w*)?\s*(\d+)", raw)
    windows = re.search(r"\bо(?:к\w*)?\s*(\d+)", raw)
    cleaned = re.sub(r"\b[до]\w*\s*\d+", " ", raw)
    cleaned = re.sub(r"\bh\s*", " ", cleaned)
    numbers = re.findall(_NUM, cleaned)
    if len(numbers) < 3:
        raise ValueError("нужно три размера: длина, ширина, высота — например «4,2 3,1 2,7»")
    length, width, height = (dec(n) for n in numbers[:3])
    if min(length, width, height) <= ZERO or max(length, width) > 200 or height > 30:
        raise ValueError("размеры не похожи на помещение — проверьте числа (метры)")
    name_match = re.match(r"^\s*([а-яa-z][а-яa-z\- ]*?)\s+\d", raw)
    name = name_match.group(1).strip().capitalize() if name_match else default_name
    return Room(
        name=name, length=length, width=width, height=height,
        doors=int(doors.group(1)) if doors else 1,
        windows=int(windows.group(1)) if windows else 1,
    )


def summary(rooms: list[Room]) -> dict[str, Decimal]:
    """Variables shared with templates: S, P, H, W, C, L, K, D, O, R."""
    if not rooms:
        return {}
    perimeter = sum((room.perimeter for room in rooms), ZERO)
    height = sum((room.height * room.perimeter for room in rooms), ZERO) / perimeter if perimeter else ZERO
    return {
        "S": money(sum((room.floor for room in rooms), ZERO)),
        "C": money(sum((room.floor for room in rooms), ZERO)),
        "P": money(perimeter),
        "H": money(height),
        "W": money(sum((room.walls for room in rooms), ZERO)),
        "L": money(sum((room.plinth for room in rooms), ZERO)),
        "K": money(sum((room.slopes for room in rooms), ZERO)),
        "D": Decimal(sum(room.doors for room in rooms)),
        "O": Decimal(sum(room.windows for room in rooms)),
        "R": Decimal(len(rooms)),
    }


def summary_text(rooms: list[Room]) -> str:
    if not rooms:
        return "📐 Помещений пока нет."
    values = summary(rooms)
    lines = [room.as_text() for room in rooms]
    lines += [
        "",
        f"📊 Итого по {len(rooms)} пом.:",
        f"• Пол / потолок: {qty_str(values['S'])} м²",
        f"• Стены за вычетом проёмов: {qty_str(values['W'])} м²",
        f"• Периметр: {qty_str(values['P'])} м, плинтус: {qty_str(values['L'])} м",
        f"• Откосы окон: {qty_str(values['K'])} м",
        f"• Дверей: {values['D']}, окон: {values['O']}",
        f"Проёмы: дверь {qty_str(DOOR_W)}×{qty_str(DOOR_H)} м, окно {qty_str(WIN_W)}×{qty_str(WIN_H)} м.",
    ]
    return "\n".join(lines)


# key, button label, text for the catalog search, unit, variable
WORKS: list[tuple[str, str, str, str, str]] = [
    ("plaster", "Штукатурка стен", "штукатурка стен по маякам", "м2", "W"),
    ("putty", "Шпатлёвка стен", "шпаклевка стен", "м2", "W"),
    ("paint", "Покраска стен", "окраска стен", "м2", "W"),
    ("wallpaper", "Обои", "оклейка стен обоями", "м2", "W"),
    ("screed", "Стяжка пола", "полусухая стяжка", "м2", "S"),
    ("laminate", "Ламинат", "укладка ламината", "м2", "S"),
    ("tile", "Плитка на пол", "укладка плитки на пол", "м2", "S"),
    ("ceilputty", "Шпатлёвка потолка", "шпаклевка потолков", "м2", "C"),
    ("ceilpaint", "Покраска потолка", "окраска потолков", "м2", "C"),
    ("stretch", "Натяжной потолок", "натяжной потолок", "м2", "C"),
    ("plinth", "Плинтус", "монтаж плинтуса", "м", "L"),
    ("slopes", "Откосы", "штукатурка откосов", "м", "K"),
]
