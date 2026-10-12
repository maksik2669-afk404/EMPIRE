"""Версии сметы и сравнение двух версий (основа для допсоглашения)."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .catalog import tokens
from .model import Estimate, Position
from .money import ZERO, money, qty_str, rub


def _key(position: Position) -> tuple[str, str]:
    return (position.code or " ".join(tokens(position.name)), position.unit)


@dataclass
class Change:
    name: str
    unit: str
    old_qty: Decimal
    new_qty: Decimal
    old_total: Decimal
    new_total: Decimal
    new_price: Decimal
    code: str = ""

    @property
    def delta_qty(self) -> Decimal:
        return self.new_qty - self.old_qty

    @property
    def delta(self) -> Decimal:
        return money(self.new_total - self.old_total)


@dataclass
class Diff:
    changes: list[Change] = field(default_factory=list)
    old_total: Decimal = ZERO
    new_total: Decimal = ZERO

    @property
    def added(self) -> list[Change]:
        return [c for c in self.changes if c.old_qty == ZERO and c.new_qty > ZERO]

    @property
    def removed(self) -> list[Change]:
        return [c for c in self.changes if c.new_qty == ZERO and c.old_qty > ZERO]

    @property
    def changed(self) -> list[Change]:
        return [c for c in self.changes if c.old_qty > ZERO and c.new_qty > ZERO]

    @property
    def extra(self) -> list[Change]:
        """Дополнительные работы: новые позиции и увеличение объёмов или цены."""
        return [c for c in self.changes if c.delta > ZERO]

    @property
    def excluded(self) -> list[Change]:
        return [c for c in self.changes if c.delta < ZERO]

    @property
    def delta(self) -> Decimal:
        return money(self.new_total - self.old_total)

    def as_text(self, limit: int = 20) -> str:
        sign = "+" if self.delta >= ZERO else "−"
        lines = [f"🔀 Было {rub(self.old_total)} ₽ → стало {rub(self.new_total)} ₽ ({sign}{rub(abs(self.delta))} ₽)"]
        if not self.changes:
            lines.append("Изменений в позициях нет.")
            return "\n".join(lines)
        for title, items in (("➕ Добавлено", self.added), ("➖ Убрано", self.removed), ("✏️ Изменено", self.changed)):
            if not items:
                continue
            lines.append("")
            lines.append(f"{title}: {len(items)}")
            for change in items[:limit]:
                if change in self.changed:
                    lines.append(f"• {change.name[:50]}: {qty_str(change.old_qty)} → {qty_str(change.new_qty)} "
                                 f"{change.unit}, {'+' if change.delta >= 0 else '−'}{rub(abs(change.delta))} ₽")
                else:
                    lines.append(f"• {change.name[:50]}: {qty_str(change.new_qty or change.old_qty)} {change.unit}, "
                                 f"{rub(abs(change.delta))} ₽")
        return "\n".join(lines)


def diff(old: Estimate, new: Estimate) -> Diff:
    """Positions are matched by rate code (or name) and unit; totals include VAT."""
    old_map: dict[tuple, Position] = {}
    for position in old.positions:
        old_map.setdefault(_key(position), position)
    new_map: dict[tuple, Position] = {}
    for position in new.positions:
        new_map.setdefault(_key(position), position)
    old_scale, new_scale = old.scale(), new.scale()
    result = Diff(old_total=old.total(), new_total=new.total())
    for key in list(old_map) + [k for k in new_map if k not in old_map]:
        before, after = old_map.get(key), new_map.get(key)
        old_total = money(before.total(old.indices) * old_scale) if before else ZERO
        new_total = money(after.total(new.indices) * new_scale) if after else ZERO
        old_qty = before.qty if before else ZERO
        new_qty = after.qty if after else ZERO
        if before and after and old_qty == new_qty and old_total == new_total:
            continue
        sample = after or before
        price = money(new_total / new_qty) if new_qty else ZERO
        result.changes.append(Change(name=sample.name, unit=sample.unit, old_qty=old_qty, new_qty=new_qty,
                                     old_total=old_total, new_total=new_total, new_price=price, code=sample.code))
    return result
