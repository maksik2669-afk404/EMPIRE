"""Выполнение работ, акты КС-2, оплаты и график платежей по смете."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from .model import Estimate, Position
from .money import ZERO, dec, money, pct, qty_str, rub

SCHEDULE_PRESETS: dict[str, list[tuple[str, int]]] = {
    "30/70": [("Аванс", 30), ("Окончательный расчёт после КС-2", 70)],
    "50/50": [("Аванс", 50), ("Окончательный расчёт после КС-2", 50)],
    "30/40/30": [("Аванс", 30), ("Промежуточный платёж", 40), ("Окончательный расчёт", 30)],
    "100": [("Оплата по факту после КС-2", 100)],
}


def set_done(estimate: Estimate, index: int, value: str) -> Position:
    """Mark completed volume: '60%', '85' (in units of the position) or 'всё'.

    Volume already closed by KS-2 acts cannot be taken back.
    """
    if not 1 <= index <= len(estimate.positions):
        raise ValueError(f"нет позиции № {index}")
    position = estimate.positions[index - 1]
    raw = (value or "").strip().lower().replace(" ", "")
    if raw in {"все", "всё", "100%", "полностью", "full"}:
        done = position.qty
    elif raw.endswith("%"):
        done = position.qty * pct(raw.rstrip("%"))
    else:
        done = dec(raw, None)
        if done is None:
            raise ValueError("нужно число, процент или «всё»")
    if done < ZERO:
        raise ValueError("выполнение не может быть отрицательным")
    if done > position.qty:
        raise ValueError(f"больше сметного объёма ({qty_str(position.qty)} {position.unit})")
    if done < position.acted:
        raise ValueError(f"уже закрыто актами {qty_str(position.acted)} {position.unit} — меньше нельзя")
    position.done = done.quantize(Decimal("0.0001")).normalize()
    return position


def _full_amount(estimate: Estimate, smr: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Positions amount -> (limited share, VAT, total). The same rounding acts use."""
    totals = estimate.totals()
    share = smr / totals.smr if totals.smr else ZERO
    limited = money(totals.limited_total * share)
    vat = money((smr + limited) * pct(estimate.vat_pct))
    return limited, vat, money(smr + limited + vat)


def _value(estimate: Estimate, attr: str) -> Decimal:
    """Value of done volumes with limited costs and VAT, rounded like an act."""
    smr = ZERO
    for position in estimate.positions:
        if position.qty:
            smr += money(position.total(estimate.indices) * getattr(position, attr) / position.qty)
    return _full_amount(estimate, money(smr))[2]


@dataclass
class Progress:
    total: Decimal
    done: Decimal
    acted: Decimal
    paid: Decimal
    acts: int
    schedule: list[dict] = field(default_factory=list)

    @property
    def done_pct(self) -> Decimal:
        return (self.done / self.total * 100).quantize(Decimal("0.1")) if self.total else ZERO

    @property
    def debt(self) -> Decimal:
        """Закрыто актами, но не оплачено. Отрицательно — переплата (аванс)."""
        return money(self.acted - self.paid)

    @property
    def overdue(self) -> list[dict]:
        return [row for row in self.schedule if row["state"] == "overdue"]

    def as_text(self) -> str:
        lines = [
            f"📈 Выполнено: {rub(self.done)} ₽ из {rub(self.total)} ₽ ({self.done_pct}%)",
            f"📝 Закрыто актами КС-2: {rub(self.acted)} ₽ (актов: {self.acts})",
            f"💵 Оплачено: {rub(self.paid)} ₽",
        ]
        if self.debt > ZERO:
            lines.append(f"❗️ Заказчик должен по актам: {rub(self.debt)} ₽")
        elif self.debt < ZERO:
            lines.append(f"💼 Аванс сверх закрытого: {rub(-self.debt)} ₽")
        if self.schedule:
            lines.append("")
            lines.append("🗓 График платежей:")
            icons = {"paid": "✅", "partial": "🟡", "wait": "⏳", "overdue": "🔴"}
            for row in self.schedule:
                due = f" до {row['due']}" if row.get("due") else ""
                lines.append(f"{icons[row['state']]} {row['name']} {row['pct']}% — {rub(row['amount'])} ₽{due}")
        return "\n".join(lines)


def progress(estimate: Estimate, today: date | None = None) -> Progress:
    today = today or date.today()
    total = estimate.total()
    paid = money(sum((dec(item.get("amount")) for item in estimate.payments), ZERO))
    rows: list[dict] = []
    covered = paid
    for item in estimate.schedule:
        amount = money(total * pct(item.get("pct")))
        due = item.get("due") or ""
        if covered >= amount:
            state = "paid"
        elif covered > ZERO:
            state = "partial"
        else:
            state = "wait"
        if state != "paid" and due and date.fromisoformat(due) < today:
            state = "overdue"
        covered = max(covered - amount, ZERO)
        rows.append({"name": item.get("name", ""), "pct": item.get("pct"), "amount": amount, "due": due, "state": state})
    acted = money(sum((dec(act["total"]) for act in estimate.acts), ZERO))
    return Progress(total=total, done=_value(estimate, "done"), acted=acted,
                    paid=paid, acts=len(estimate.acts), schedule=rows)


def add_payment(estimate: Estimate, amount, *, when: date | None = None, note: str = "") -> dict:
    value = money(amount)
    if value <= ZERO:
        raise ValueError("сумма оплаты должна быть больше нуля")
    item = {"date": (when or date.today()).isoformat(), "amount": str(value), "note": note}
    estimate.payments.append(item)
    return item


def set_schedule(estimate: Estimate, preset: str, *, start: date | None = None, step_days: int = 14) -> list[dict]:
    if preset not in SCHEDULE_PRESETS:
        raise ValueError(f"нет такого графика: {preset}")
    start = start or date.today()
    estimate.schedule = [
        {"name": name, "pct": share, "due": (start + timedelta(days=step_days * number)).isoformat()}
        for number, (name, share) in enumerate(SCHEDULE_PRESETS[preset])
    ]
    return estimate.schedule


def make_act(estimate: Estimate, *, period_from: date | None = None, period_to: date | None = None,
             when: date | None = None) -> dict:
    """Close everything done but not yet acted into a new KS-2 act."""
    when = when or date.today()
    items: list[list] = []
    smr = ZERO
    for index, position in enumerate(estimate.positions, 1):
        volume = position.to_act
        if volume <= ZERO or not position.qty:
            continue
        amount = money(position.total(estimate.indices) * volume / position.qty)
        items.append([index, str(volume), str(amount)])
        smr += amount
    if not items:
        raise ValueError("нечего закрывать: отметьте выполненные объёмы")
    limited, vat, _ = _full_amount(estimate, money(smr))
    previous = estimate.acts[-1]["to"] if estimate.acts else ""
    act = {
        "number": len(estimate.acts) + 1,
        "date": when.isoformat(),
        "from": (period_from or (date.fromisoformat(previous) + timedelta(days=1) if previous else estimate.date)).isoformat(),
        "to": (period_to or when).isoformat(),
        "items": items,
        "smr": str(money(smr)),
        "limited": str(limited),
        "vat": str(vat),
        "total": str(money(smr + limited + vat)),
    }
    for index, volume, _ in items:
        estimate.positions[index - 1].acted += dec(volume)
    estimate.acts.append(act)
    return act


def year_to_date(estimate: Estimate, act: dict) -> tuple[Decimal, Decimal]:
    """(с начала года, с начала работ) по актам до этого включительно, с НДС."""
    year = act["date"][:4]
    upto = [item for item in estimate.acts if item["number"] <= act["number"]]
    since_start = money(sum((dec(item["total"]) for item in upto), ZERO))
    in_year = money(sum((dec(item["total"]) for item in upto if item["date"][:4] == year), ZERO))
    return in_year, since_start
