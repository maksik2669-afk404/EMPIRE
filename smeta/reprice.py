"""Пересчёт сметы по новым индексам ФГИС ЦС и новому прайсу — с письмом заказчику."""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .catalog import Indices
from .materials import OfferBook
from .model import MATERIAL, Estimate
from .money import ZERO, money, rub


@dataclass
class RepriceRow:
    name: str
    old: Decimal
    new: Decimal

    @property
    def delta(self) -> Decimal:
        return money(self.new - self.old)

    @property
    def pct(self) -> Decimal:
        return ((self.new - self.old) / self.old * 100).quantize(Decimal("0.1")) if self.old else ZERO


@dataclass
class RepriceResult:
    estimate: Estimate
    rows: list[RepriceRow] = field(default_factory=list)
    old_total: Decimal = ZERO
    new_total: Decimal = ZERO
    reason: str = ""

    @property
    def delta(self) -> Decimal:
        return money(self.new_total - self.old_total)

    @property
    def pct(self) -> Decimal:
        return ((self.new_total - self.old_total) / self.old_total * 100).quantize(Decimal("0.1")) if self.old_total else ZERO

    def as_text(self, limit: int = 12) -> str:
        sign = "+" if self.delta >= 0 else "−"
        lines = [f"🔁 {self.reason}",
                 f"Было {rub(self.old_total)} ₽ → стало {rub(self.new_total)} ₽ ({sign}{rub(abs(self.delta))} ₽, {sign}{abs(self.pct)}%)"]
        changed = sorted((row for row in self.rows if row.delta), key=lambda row: -abs(row.delta))
        for row in changed[:limit]:
            lines.append(f"• {row.name[:50]}: {'+' if row.delta >= 0 else '−'}{rub(abs(row.delta))} ₽ ({row.pct:+}%)")
        if not changed:
            lines.append("Цены позиций не изменились.")
        return "\n".join(lines)

    def letter(self, original: Estimate) -> str:
        company = original.company.name or "Подрядчик"
        customer = original.customer or "Заказчик"
        contract = f" по договору {original.contract}" if original.contract else ""
        return (
            f"{customer}\n\n"
            f"Уведомляем об изменении сметной стоимости работ{contract} "
            f"(смета № {original.number or '—'} от {original.date.strftime('%d.%m.%Y')}).\n\n"
            f"Основание: {self.reason}.\n"
            f"Стоимость по смете была {rub(self.old_total)} ₽, после пересчёта составляет "
            f"{rub(self.new_total)} ₽ ({'+' if self.delta >= 0 else '−'}{rub(abs(self.delta))} ₽, "
            f"{'+' if self.delta >= 0 else '−'}{abs(self.pct)}%).\n\n"
            f"Расчёт по позициям прилагаем. Предлагаем оформить дополнительное соглашение к договору.\n\n"
            f"С уважением,\n{original.company.signer_title} {company} {original.company.signer}".rstrip()
        )


def reprice(estimate: Estimate, *, indices: Indices | None = None, offers: OfferBook | None = None) -> RepriceResult:
    """A repriced copy. Normative positions follow the new index, materials follow the price list."""
    fresh = estimate.copy()
    reasons: list[str] = []
    if indices is not None:
        fresh.indices = indices
        reasons.append(f"индексы {indices.region} {indices.period}".strip())
    if offers is not None:
        updated = 0
        for position in fresh.positions:
            if position.kind != MATERIAL or position.normative:
                continue
            offer = offers.best(position.name, position.unit)
            if offer is None:
                continue
            position.unit_price = offer.sell
            position.unit_cost = offer.net
            updated += 1
        if updated:
            reasons.append(f"новый прайс поставщиков ({updated} поз.)")
    old_scale, new_scale = estimate.scale(), fresh.scale()
    rows = [RepriceRow(name=old.name, old=money(old.total(estimate.indices) * old_scale),
                       new=money(new.total(fresh.indices) * new_scale))
            for old, new in zip(estimate.positions, fresh.positions)]
    return RepriceResult(estimate=fresh, rows=rows, old_total=estimate.total(), new_total=fresh.total(),
                         reason=", ".join(reasons) or "без изменений")
