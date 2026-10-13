"""Tax calculator: what is left of an estimate after taxes, per tax regime.

Rates and limits live in data/tax/rates.csv - one row per value, with a year. The engine
never hard-codes a percentage, and every result says which year's rates it used, so an
outdated row is visible instead of silently wrong.

Regimes: УСН 6 %, УСН 15 %, ОСНО (ООО), ОСНО (ИП), НПД (самозанятый).
"""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path

from .money import ZERO, dec, money, pct, rub

RATES_PATH = Path(__file__).resolve().parent.parent / "data" / "tax" / "rates.csv"

USN6 = "usn6"
USN15 = "usn15"
OSNO_OOO = "osno_ooo"
OSNO_IP = "osno_ip"
NPD = "npd"
REGIMES = (USN6, USN15, OSNO_OOO, OSNO_IP, NPD)
REGIME_TITLES = {
    USN6: "УСН «доходы» 6 %",
    USN15: "УСН «доходы минус расходы» 15 %",
    OSNO_OOO: "ОСНО, ООО (НДС + налог на прибыль)",
    OSNO_IP: "ОСНО, ИП (НДС + НДФЛ)",
    NPD: "НПД, самозанятый 6 %",
}


@dataclass
class TaxRates:
    year: int
    values: dict[str, str] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    requested_year: int | None = None

    def num(self, key: str, default=ZERO) -> Decimal:
        return dec(self.values.get(key), dec(default))

    def brackets(self, key: str = "ndfl_brackets") -> list[tuple[Decimal | None, Decimal]]:
        """'2400000:13,5000000:15,:22' -> [(2400000, 13), (5000000, 15), (None, 22)]."""
        out: list[tuple[Decimal | None, Decimal]] = []
        for chunk in (self.values.get(key) or "").split(","):
            limit, _, rate = chunk.partition(":")
            if not rate.strip():
                continue
            out.append((dec(limit) if limit.strip() else None, dec(rate)))
        return out

    @property
    def stale(self) -> bool:
        return self.requested_year is not None and self.requested_year != self.year

    @classmethod
    def load(cls, year: int | None = None, path: Path | str = RATES_PATH) -> "TaxRates":
        wanted = year or date.today().year
        rows: list[tuple[int, str, str, str]] = []
        source = Path(path)
        if source.exists():
            lines = [line for line in source.read_text(encoding="utf-8").splitlines()
                     if line.strip() and not line.lstrip().startswith("#")]
            for row in csv.reader(io.StringIO("\n".join(lines[1:])), delimiter=";"):
                if len(row) >= 3 and row[0].strip().isdigit():
                    rows.append((int(row[0]), row[1].strip(), row[2].strip(), row[3].strip() if len(row) > 3 else ""))
        years = sorted({row[0] for row in rows})
        if not years:
            raise ValueError("справочник налоговых ставок недоступен — сообщите в поддержку")
        chosen = max((y for y in years if y <= wanted), default=min(years))
        values = {key: value for y, key, value, _ in rows if y == chosen}
        notes = {key: note for y, key, _, note in rows if y == chosen}
        return cls(year=chosen, values=values, notes=notes, requested_year=wanted)

    def as_text(self) -> str:
        lines = [f"Ставки налогов, {self.year} год:"]
        for key, value in self.values.items():
            note = self.notes.get(key, key)
            lines.append(f"  {note}: {value}")
        lines.append("Справочные ставки для расчётов — перед сдачей отчётности сверьтесь с НК РФ.")
        return "\n".join(lines)


@dataclass
class Money:
    """Inputs of a tax calculation. All amounts in rubles, VAT included where stated."""

    revenue: Decimal                      # выручка по смете (с НДС, если он есть в смете)
    vat_in_revenue: Decimal = ZERO        # сумма НДС внутри выручки (0, если смета без НДС)
    materials: Decimal = ZERO             # закупка материалов (с НДС поставщика)
    payroll: Decimal = ZERO               # ФОТ рабочих (до налогов)
    other_costs: Decimal = ZERO           # прочие расходы (техника, аренда, топливо)
    suppliers_with_vat: bool = True       # поставщики на ОСНО -> входной НДС к вычету
    employees: bool = True                # есть работники по трудовым договорам
    ip: bool = False                      # ИП (платит взносы за себя), иначе ООО
    annual_revenue: Decimal | None = None  # годовой доход, если известен (для лимитов и НДС)

    def __post_init__(self) -> None:
        for name in ("revenue", "vat_in_revenue", "materials", "payroll", "other_costs"):
            setattr(self, name, dec(getattr(self, name)))
        if self.annual_revenue is not None:
            self.annual_revenue = dec(self.annual_revenue)

    @property
    def revenue_net(self) -> Decimal:
        return money(self.revenue - self.vat_in_revenue)

    @property
    def year_revenue(self) -> Decimal:
        return self.annual_revenue if self.annual_revenue is not None else self.revenue

    @property
    def input_vat(self) -> Decimal:
        """Входной НДС в закупке материалов (ставка/(100+ставка)), если поставщики с НДС."""
        if not self.suppliers_with_vat or not self.materials:
            return ZERO
        rate = current_vat()                      # действующая ставка из data/tax/rates.csv
        return money(self.materials * rate / (Decimal(100) + rate))

    @property
    def costs_net(self) -> Decimal:
        """Расходы без НДС: материалы минус вычет, ФОТ и прочее."""
        return money(self.materials - self.input_vat + self.payroll + self.other_costs)


@dataclass
class TaxResult:
    regime: str
    year: int
    items: dict[str, Decimal] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    blocked: str = ""                     # режим недоступен (превышен лимит)

    @property
    def title(self) -> str:
        return REGIME_TITLES.get(self.regime, self.regime)

    @property
    def total(self) -> Decimal:
        return money(sum(self.items.values()))

    def net(self, inputs: Money) -> Decimal:
        """Сколько останется после расходов и налогов."""
        return money(inputs.revenue - inputs.materials - inputs.payroll - inputs.other_costs - self.total)

    def burden(self, inputs: Money) -> Decimal:
        if inputs.revenue <= ZERO:
            return ZERO
        return (self.total / inputs.revenue * Decimal(100)).quantize(Decimal("0.1"))

    def as_text(self, inputs: Money) -> str:
        lines = [f"{self.title}"]
        if self.blocked:
            lines.append(f"  ❌ {self.blocked}")
            return "\n".join(lines)
        for name, value in self.items.items():
            lines.append(f"  {name}: {rub(value)} ₽")
        lines.append(f"  Налогов всего: {rub(self.total)} ₽ ({self.burden(inputs)}% от суммы сметы)")
        lines.append(f"  Остаётся: {rub(self.net(inputs))} ₽")
        for note in self.notes:
            lines.append(f"  • {note}")
        return "\n".join(lines)


# ---------------------------------------------------------------- insurance


def insurance_contributions(inputs: Money, rates: TaxRates) -> tuple[Decimal, list[str]]:
    """Взносы с ФОТ: 30 % до предельной базы + травматизм."""
    if not inputs.payroll or not inputs.employees:
        return ZERO, []
    limit = rates.num("insurance_base_limit")
    main_rate = pct(rates.num("insurance_rate"))
    reduced = pct(rates.num("insurance_reduced_rate"))
    accident = pct(rates.num("accident_rate"))
    base = inputs.payroll
    notes: list[str] = []
    if limit and base > limit:
        amount = money(limit * main_rate + (base - limit) * reduced)
        notes.append(
            f"часть ФОТ свыше предельной базы ({rub(limit)} ₽ на человека) — "
            f"по пониженной ставке {rates.num('insurance_reduced_rate')}%"
        )
    else:
        amount = money(base * main_rate)
    amount = money(amount + base * accident)
    notes.append("предельная база считается на одного работника — при нескольких сотрудниках сумма будет ниже")
    return amount, notes


def ip_contributions(inputs: Money, rates: TaxRates, base: Decimal) -> Decimal:
    """Фиксированные взносы ИП + 1 % с превышения."""
    fixed = rates.num("ip_fixed")
    threshold = rates.num("ip_extra_threshold")
    extra_rate = pct(rates.num("ip_extra_rate"))
    cap = rates.num("ip_extra_cap")
    extra = ZERO
    if base > threshold:
        extra = money((base - threshold) * extra_rate)
        if cap:
            extra = min(extra, cap)
    return money(fixed + extra)


def ndfl(amount: Decimal, rates: TaxRates) -> Decimal:
    """Прогрессивный НДФЛ по шкале из ставок."""
    total = ZERO
    previous = ZERO
    for limit, rate in rates.brackets():
        top = limit if limit is not None else amount
        chunk = min(amount, top) - previous
        if chunk > ZERO:
            total += chunk * pct(rate)
        previous = top
        if limit is not None and amount <= limit:
            break
    if previous < amount:                      # последняя ставка без ограничения
        last_rate = rates.brackets()[-1][1] if rates.brackets() else ZERO
        total += (amount - previous) * pct(last_rate)
    return money(total)


def usn_vat(inputs: Money, rates: TaxRates) -> tuple[Decimal, list[str]]:
    """НДС на УСН: с 2025 года появляется при доходе выше порога."""
    threshold = rates.num("usn_vat_threshold")
    year_revenue = inputs.year_revenue
    if not threshold or year_revenue <= threshold:
        return ZERO, []
    low_limit = rates.num("usn_vat_low_limit")
    rate = rates.num("usn_vat_rate_low") if year_revenue <= low_limit else rates.num("usn_vat_rate_mid")
    amount = money(inputs.revenue_net * pct(rate))
    return amount, [
        f"доход за год выше {rub(threshold)} ₽ — на УСН начисляется НДС {rate:g}% без права на вычеты "
        f"(альтернатива — {rates.num('vat_rate'):g} % с вычетами, тогда считайте как ОСНО)"
    ]


# ---------------------------------------------------------------- regimes


def calculate(regime: str, inputs: Money, rates: TaxRates | None = None) -> TaxResult:
    rates = rates or TaxRates.load()
    result = TaxResult(regime=regime, year=rates.year)
    if rates.stale:
        result.notes.append(
            f"в файле ставок нет {rates.requested_year} года — считаю по ставкам {rates.year} года"
        )

    if regime == NPD:
        limit = rates.num("npd_limit")
        if inputs.year_revenue > limit:
            result.blocked = f"доход выше лимита НПД ({rub(limit)} ₽ в год)"
            return result
        if inputs.payroll and inputs.employees:
            result.blocked = "самозанятый не может нанимать работников по трудовым договорам"
            return result
        result.items["НПД 6 %"] = money(inputs.revenue * pct(rates.num("npd_rate_org")))
        if inputs.payroll:
            result.notes.append("ФОТ учтён как выплаты подрядчикам, а не работникам")
        return result

    if regime in (USN6, USN15):
        limit = rates.num("usn_income_limit")
        if inputs.year_revenue > limit:
            result.blocked = f"доход выше лимита УСН ({rub(limit)} ₽ в год) — остаётся ОСНО"
            return result
        vat, vat_notes = usn_vat(inputs, rates)
        if vat:
            result.items["НДС на УСН"] = vat
            result.notes.extend(vat_notes)
        contributions, notes = insurance_contributions(inputs, rates)
        if contributions:
            result.items["Страховые взносы с ФОТ"] = contributions
            result.notes.extend(notes)
        own = ip_contributions(inputs, rates, inputs.revenue_net) if inputs.ip else ZERO
        if own:
            result.items["Взносы ИП за себя"] = own
        if regime == USN6:
            tax = money(inputs.revenue_net * pct(rates.num("usn_income_rate")))
            paid = money(contributions + own)
            # ИП без работников уменьшает налог на взносы полностью, остальные - не более 50 %
            ceiling = tax if (inputs.ip and not inputs.employees) else money(tax * Decimal("0.5"))
            reduction = min(paid, ceiling)
            if reduction:
                tax = max(tax - reduction, ZERO)
                result.notes.append(
                    f"налог уменьшен на взносы {rub(reduction)} ₽ "
                    + ("(ИП без работников — без ограничения)" if ceiling == tax + reduction and inputs.ip and not inputs.employees
                       else "(не более 50 % налога)")
                )
            result.items["УСН 6 %"] = tax
            return result
        base = money(inputs.revenue_net - inputs.costs_net - contributions - own)
        tax = money(max(base, ZERO) * pct(rates.num("usn_profit_rate")))
        minimum = money(inputs.revenue_net * pct(rates.num("usn_min_tax_rate")))
        if tax < minimum:
            tax = minimum
            result.notes.append(f"сработал минимальный налог {rates.num('usn_min_tax_rate'):g}% от дохода")
        result.items["УСН 15 %"] = tax
        return result

    # ОСНО
    vat_payable = ZERO
    if inputs.vat_in_revenue:
        vat_payable = money(max(inputs.vat_in_revenue - inputs.input_vat, ZERO))
        result.items["НДС к уплате"] = vat_payable
        if inputs.input_vat:
            result.notes.append(f"из НДС вычтен входной НДС поставщиков {rub(inputs.input_vat)} ₽")
    else:
        result.notes.append(f"в смете нет НДС, а на ОСНО его нужно начислить — поднимите цену на {rates.num('vat_rate'):g} % или смените режим")
    contributions, notes = insurance_contributions(inputs, rates)
    if contributions:
        result.items["Страховые взносы с ФОТ"] = contributions
        result.notes.extend(notes)
    profit = money(inputs.revenue_net - inputs.costs_net - contributions)
    if regime == OSNO_OOO:
        result.items["Налог на прибыль"] = money(max(profit, ZERO) * pct(rates.num("profit_tax_rate")))
        return result
    own = ip_contributions(inputs, rates, inputs.revenue_net)
    result.items["Взносы ИП за себя"] = own
    result.items["НДФЛ"] = ndfl(money(max(profit - own, ZERO)), rates)
    result.notes.append("НДФЛ считается по годовой прогрессивной шкале — по одной смете это оценка")
    return result


def compare(inputs: Money, rates: TaxRates | None = None, regimes=REGIMES) -> list[TaxResult]:
    """All regimes, cheapest first. Blocked ones go last."""
    rates = rates or TaxRates.load()
    results = [calculate(regime, inputs, rates) for regime in regimes]
    results.sort(key=lambda item: (bool(item.blocked), item.total))
    return results


def compare_text(inputs: Money, rates: TaxRates | None = None) -> str:
    rates = rates or TaxRates.load()
    results = compare(inputs, rates)
    lines = [
        f"🧾 Налоги по смете {rub(inputs.revenue)} ₽ (ставки {rates.year} года)",
        f"Расходы: материалы {rub(inputs.materials)} ₽, ФОТ {rub(inputs.payroll)} ₽, "
        f"прочее {rub(inputs.other_costs)} ₽",
        "",
    ]
    for result in results:
        lines.append(result.as_text(inputs))
        lines.append("")
    best = next((item for item in results if not item.blocked), None)
    if best:
        lines.append(f"Выгоднее всего: {best.title} — остаётся {rub(best.net(inputs))} ₽")
        others = [item for item in results if not item.blocked and item is not best]
        if others:
            worst = max(others, key=lambda item: item.total)
            lines.append(f"Разница с худшим вариантом ({worst.title}): {rub(worst.total - best.total)} ₽")
    lines.append("")
    lines.append("Это расчёт для планирования, а не налоговая декларация: лимиты и прогрессия "
                 "считаются от годового дохода, его можно задать точнее.")
    return "\n".join(lines)


def price_for(target_net, regime: str, *, materials=ZERO, payroll=ZERO, other_costs=ZERO, vat_pct=None,
              employees: bool = True, ip: bool = False, annual_revenue=None, suppliers_with_vat: bool = True,
              rates: TaxRates | None = None) -> tuple[Decimal, TaxResult, Money]:
    """Smallest estimate total that leaves `target_net` after costs and taxes (to the kopeck)."""
    rates = rates or TaxRates.load()
    target = money(target_net)
    vat_rate = rates.num("vat_rate") if vat_pct is None else dec(vat_pct)

    def run(revenue: Decimal) -> tuple[Decimal, TaxResult, Money]:
        vat = money(revenue * vat_rate / (100 + vat_rate)) if vat_rate else ZERO
        inputs = Money(revenue=revenue, vat_in_revenue=vat, materials=materials, payroll=payroll,
                       other_costs=other_costs, employees=employees, ip=ip,
                       annual_revenue=annual_revenue, suppliers_with_vat=suppliers_with_vat)
        result = calculate(regime, inputs, rates)
        return result.net(inputs), result, inputs

    low = ZERO
    high = money((dec(materials) + dec(payroll) + dec(other_costs) + target) * 3 + 1000)
    net, result, inputs = run(high)
    if result.blocked:
        return high, result, inputs
    for _ in range(12):                       # раздвигаем верхнюю границу, если налоги съели всё
        if net >= target:
            break
        high *= 2
        net, result, inputs = run(high)
    for _ in range(80):                       # бисекция до копейки
        if high - low <= Decimal("0.01"):
            break
        middle = money((low + high) / 2)
        net, _, _ = run(middle)
        if net >= target:
            high = middle
        else:
            low = middle
    net, result, inputs = run(high)
    return high, result, inputs


def current_vat(year: int | None = None) -> Decimal:
    """Текущая основная ставка НДС (%) из справочника data/tax/rates.csv."""
    return TaxRates.load(year).num("vat_rate")
