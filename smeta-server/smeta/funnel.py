"""Статусы смет, воронка продаж и напоминания по КП без ответа."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .model import Estimate
from .money import ZERO, money, rub

STATUSES: list[tuple[str, str, str]] = [
    ("draft", "📝", "Черновик"),
    ("sent", "📤", "Отправлено заказчику"),
    ("agreed", "🤝", "Согласовано"),
    ("work", "🏗", "В работе"),
    ("done", "✅", "Закрыто"),
    ("lost", "❌", "Проиграно"),
]
TITLES = {code: f"{icon} {title}" for code, icon, title in STATUSES}
WON = {"agreed", "work", "done"}
REMIND_DAYS = 3


def set_status(estimate: Estimate, status: str, note: str = "", now: datetime | None = None) -> None:
    if status not in TITLES:
        raise ValueError(f"нет статуса {status}")
    now = now or datetime.now(timezone.utc)
    estimate.status = status
    estimate.status_log.append({"status": status, "at": now.isoformat(timespec="seconds"), "note": note})
    if status == "sent":
        estimate.sent_at = now.isoformat(timespec="seconds")


def remind_at(now: datetime | None = None, days: int = REMIND_DAYS) -> datetime:
    return (now or datetime.now(timezone.utc)) + timedelta(days=days)


@dataclass
class Stats:
    counts: dict[str, int] = field(default_factory=dict)
    sums: dict[str, Decimal] = field(default_factory=dict)
    lost_reasons: dict[str, int] = field(default_factory=dict)
    period_days: int = 30

    @property
    def offered(self) -> int:
        return sum(self.counts.get(code, 0) for code in ("sent", "agreed", "work", "done", "lost"))

    @property
    def won(self) -> int:
        return sum(self.counts.get(code, 0) for code in WON)

    @property
    def conversion(self) -> Decimal:
        return (Decimal(self.won) / Decimal(self.offered) * 100).quantize(Decimal("0.1")) if self.offered else ZERO

    @property
    def average(self) -> Decimal:
        count = self.offered
        total = sum((self.sums.get(code, ZERO) for code in ("sent", "agreed", "work", "done", "lost")), ZERO)
        return money(total / count) if count else ZERO

    @property
    def in_work(self) -> Decimal:
        return money(self.sums.get("agreed", ZERO) + self.sums.get("work", ZERO))

    def as_text(self) -> str:
        lines = [f"📊 Воронка за {self.period_days} дней"]
        for code, icon, title in STATUSES:
            count = self.counts.get(code, 0)
            if count:
                lines.append(f"{icon} {title}: {count} — {rub(self.sums.get(code, ZERO))} ₽")
        if not self.counts:
            lines.append("Смет за период нет.")
            return "\n".join(lines)
        lines += ["",
                  f"🎯 Конверсия отправленных в согласованные: {self.conversion}%",
                  f"💰 Средний чек: {rub(self.average)} ₽",
                  f"🏗 Сумма в работе: {rub(self.in_work)} ₽"]
        if self.lost_reasons:
            lines.append("")
            lines.append("Почему проигрываем:")
            for reason, count in sorted(self.lost_reasons.items(), key=lambda item: -item[1])[:5]:
                lines.append(f"• {reason} — {count}")
        return "\n".join(lines)


def stats(estimates: list[Estimate], now: datetime | None = None, days: int = 30) -> Stats:
    now = now or datetime.now(timezone.utc)
    since = (now - timedelta(days=days)).date()
    out = Stats(period_days=days)
    for estimate in estimates:
        if estimate.date < since and not estimate.status_log:
            continue
        last = estimate.status_log[-1]["at"][:10] if estimate.status_log else estimate.date.isoformat()
        if last < since.isoformat():
            continue
        out.counts[estimate.status] = out.counts.get(estimate.status, 0) + 1
        out.sums[estimate.status] = out.sums.get(estimate.status, ZERO) + estimate.total()
        if estimate.status == "lost":
            reason = (estimate.status_log[-1].get("note") if estimate.status_log else "") or "причина не указана"
            out.lost_reasons[reason] = out.lost_reasons.get(reason, 0) + 1
    return out
