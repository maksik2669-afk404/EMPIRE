"""Internal margin report: what the contractor actually keeps.

This never goes into the customer's estimate. `ProfitReport.as_text()` is written for a
private Telegram message, `export_xlsx.margin_to_xlsx` for a file marked internal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from .materials import CASH, CASHLESS, OfferBook
from .model import MATERIAL, Estimate, Position
from .money import ZERO, money, rub
from .units import norm_unit


@dataclass
class ProfitRow:
    name: str
    qty: Decimal
    unit: str
    sell: Decimal                 # сумма в смете заказчику
    cost: Decimal | None          # себестоимость, если известна
    source: str = ""              # поставщик / основание себестоимости
    payment: str = CASHLESS

    @property
    def margin(self) -> Decimal | None:
        return None if self.cost is None else money(self.sell - self.cost)

    @property
    def margin_pct(self) -> Decimal | None:
        if self.cost is None or self.sell <= ZERO:
            return None
        return ((self.sell - self.cost) / self.sell * Decimal(100)).quantize(Decimal("0.1"))

    @property
    def loss(self) -> bool:
        margin = self.margin
        return margin is not None and margin < ZERO


@dataclass
class ProfitReport:
    works: list[ProfitRow] = field(default_factory=list)
    materials: list[ProfitRow] = field(default_factory=list)
    floor_with_nr: bool = True

    @property
    def rows(self) -> list[ProfitRow]:
        return self.works + self.materials

    def _sum(self, rows: list[ProfitRow], attr: str) -> Decimal:
        total = ZERO
        for row in rows:
            value = getattr(row, attr)
            if value is not None:
                total += value
        return money(total)

    @property
    def sell_total(self) -> Decimal:
        return self._sum(self.rows, "sell")

    @property
    def cost_total(self) -> Decimal:
        return self._sum(self.rows, "cost")

    @property
    def margin_total(self) -> Decimal:
        return money(self.sell_total - self.cost_total)

    @property
    def margin_pct(self) -> Decimal:
        if self.sell_total <= ZERO:
            return ZERO
        return (self.margin_total / self.sell_total * Decimal(100)).quantize(Decimal("0.1"))

    @property
    def works_margin(self) -> Decimal:
        return money(self._sum(self.works, "sell") - self._sum(self.works, "cost"))

    @property
    def materials_margin(self) -> Decimal:
        return money(self._sum(self.materials, "sell") - self._sum(self.materials, "cost"))

    @property
    def by_payment(self) -> dict[str, Decimal]:
        out = {CASHLESS: ZERO, CASH: ZERO}
        for row in self.materials:
            if row.cost is not None:
                out[row.payment] = out.get(row.payment, ZERO) + row.cost
        return {key: money(value) for key, value in out.items() if value}

    @property
    def unknown_cost(self) -> list[ProfitRow]:
        return [row for row in self.rows if row.cost is None]

    @property
    def losses(self) -> list[ProfitRow]:
        return [row for row in self.rows if row.loss]

    def as_text(self) -> str:
        """Short private summary for Telegram (HTML-safe plain text)."""
        lines = ["💰 Профит (только для вас, в смету заказчику не попадает)", ""]
        if self.works:
            lines.append(f"Работы: {rub(self._sum(self.works, 'sell'))} ₽")
            lines.append(
                f"  себестоимость {rub(self._sum(self.works, 'cost'))} ₽"
                + (" (с накладными)" if self.floor_with_nr else " (без накладных)")
            )
            lines.append(f"  маржа {rub(self.works_margin)} ₽")
        if self.materials:
            lines.append(f"Материалы: в смете {rub(self._sum(self.materials, 'sell'))} ₽")
            lines.append(f"  закупка со скидкой {rub(self._sum(self.materials, 'cost'))} ₽")
            lines.append(f"  экономия {rub(self.materials_margin)} ₽")
            payments = self.by_payment
            if len(payments) > 1 or CASH in payments:
                lines.append(
                    "  в т.ч. " + ", ".join(f"{key}: {rub(value)} ₽" for key, value in payments.items())
                )
        lines += ["", f"ИТОГО в карман: {rub(self.margin_total)} ₽ ({self.margin_pct}% от суммы сметы)"]
        if self.losses:
            lines.append("")
            lines.append("⚠️ Ниже себестоимости:")
            for row in self.losses[:10]:
                lines.append(f"  • {row.name}: {rub(row.margin)} ₽")
        if self.unknown_cost:
            lines.append("")
            lines.append(
                f"ℹ️ Себестоимость не известна: {len(self.unknown_cost)} поз. — считаю их без маржи. "
                "Добавьте прайс поставщика (/import) или цену закупки."
            )
        return "\n".join(lines)


def build_report(estimate: Estimate, offers: OfferBook | None = None) -> ProfitReport:
    """Pair every position with a cost: norms for works, supplier offers for materials."""
    report = ProfitReport(floor_with_nr=estimate.floor_with_nr)
    for position in estimate.positions:
        sell = position.total(estimate.indices)
        if position.kind == MATERIAL:
            offer = offers.best(position.name, position.unit) if offers else None
            cost = position.floor(estimate.indices, estimate.floor_with_nr)
            source = "цена закупки задана" if cost is not None else ""
            payment = CASHLESS
            if offer is not None:
                cost = money(offer.net * position.qty)
                source = f"{offer.supplier} (−{offer.discount_pct}%)"
                payment = offer.payment
            report.materials.append(
                ProfitRow(
                    name=position.name,
                    qty=position.qty,
                    unit=norm_unit(position.unit),
                    sell=sell,
                    cost=cost,
                    source=source,
                    payment=payment,
                )
            )
            continue
        floor = position.floor(estimate.indices, estimate.floor_with_nr)
        report.works.append(
            ProfitRow(
                name=position.name,
                qty=position.qty,
                unit=norm_unit(position.unit),
                sell=sell,
                cost=floor,
                source=position.code or ("договорная цена" if not position.normative else ""),
            )
        )
    return report


def materials_for(estimate: Estimate, offers: OfferBook, consumption: dict[str, tuple[str, Decimal]] | None = None) -> list[Position]:
    """Suggest material positions for the works already in the estimate.

    `consumption` maps a material name to (unit, quantity per unit of work). Without it the
    function only reuses explicit material positions, so nothing is invented.
    """
    out: list[Position] = []
    for name, (unit, per_unit) in (consumption or {}).items():
        offer = offers.best(name, unit)
        if offer is None:
            continue
        qty = money(per_unit)
        out.append(
            Position.commercial(offer.material, qty, offer.unit, offer.sell, kind=MATERIAL, cost=offer.net)
        )
    return out
