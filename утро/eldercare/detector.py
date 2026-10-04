"""Обнаружение нештатных ситуаций с лестницей эскалации.

Главный принцип: прежде чем тревожить родню, устройство спрашивает самого
человека. Это убивает ложные тревоги и возвращает ему контроль — он отвечает,
а не является объектом наблюдения.

Настройка — на специфичность, не на чувствительность. Одна ложная тревога в
месяц выключает продукт навсегда; пропуск маловероятного события — нет.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .baseline import Baseline
from .events import Event, EventKind, Zone, bucket_of, minutes_of_day

# Сколько человек имеет на то, чтобы нажать кнопку и отменить тревогу.
CONFIRM_WINDOW = timedelta(minutes=10)
# Повторно по тому же правилу не беспокоим, пока не пройдёт столько.
RULE_COOLDOWN = timedelta(hours=6)
# «Не встал»: сколько ждать после обычного времени подъёма.
OVERSLEEP_GRACE = timedelta(hours=3)
# «Застрял в санузле»: непрерывное движение там дольше этого.
BATHROOM_STUCK = timedelta(minutes=40)
# Если в санузле нет движения столько — человек оттуда тихо ушёл. Без этого
# один ночной визит в 1:33 превращается в ложную тревогу через 40 минут.
BATHROOM_IDLE_RESET = timedelta(minutes=12)
# Устройство молчит дольше — это техническая тревога родне, без опроса человека.
OFFLINE_TIMEOUT = timedelta(minutes=25)
# На аккумуляторе дольше — у человека нет света, родне стоит знать.
POWER_LOST_GRACE = timedelta(minutes=20)


class Rule(enum.StrEnum):
    NO_ACTIVITY = "нет активности"
    OVERSLEPT = "не встал"
    BATHROOM_STUCK_RULE = "долго в санузле"
    DEVICE_OFFLINE = "устройство офлайн"
    POWER_LOST = "нет электричества"


class Severity(enum.IntEnum):
    DIGEST = 0     # попадёт в суточную сводку, никого не будит
    ALERT = 1      # сообщение родне сейчас
    URGENT = 2     # сообщение родне + звонок


@dataclass
class Prompt:
    """Устройство спрашивает человека: загорается и говорит голосом."""

    at: datetime
    rule: Rule
    text: str = "Нажмите кнопку, если всё хорошо"


@dataclass
class FamilyAlert:
    """То, что уходит в Telegram родне. Человек не отменил опрос."""

    at: datetime
    rule: Rule
    severity: Severity
    text: str


@dataclass
class _Pending:
    rule: Rule
    asked_at: datetime
    severity: Severity
    text: str


@dataclass
class Detector:
    baseline: Baseline
    last_activity: datetime | None = None
    last_heartbeat: datetime | None = None
    on_battery_since: datetime | None = None
    bathroom_since: datetime | None = None
    bathroom_last: datetime | None = None
    day_started: datetime | None = None
    saw_activity_today: bool = False

    pending: _Pending | None = None
    _cooldown: dict[Rule, datetime] = field(default_factory=dict)
    prompts: list[Prompt] = field(default_factory=list)
    alerts: list[FamilyAlert] = field(default_factory=list)
    cancelled: int = 0

    # ---------- приём событий ----------

    def feed(self, e: Event) -> None:
        if self.day_started is None or e.at.date() != self.day_started.date():
            self.day_started = e.at.replace(hour=0, minute=0, second=0, microsecond=0)
            self.saw_activity_today = False

        if e.kind is EventKind.HEARTBEAT:
            self.last_heartbeat = e.at
            return
        if e.kind is EventKind.POWER_LOST:
            self.on_battery_since = e.at
            return
        if e.kind is EventKind.POWER_RESTORED:
            self.on_battery_since = None
            return

        if e.is_activity:
            self.last_activity = e.at
            self.last_heartbeat = e.at
            if minutes_of_day(e.at) >= 240:
                self.saw_activity_today = True
            # Нажатие кнопки отменяет текущий опрос — человек ответил.
            if e.kind is EventKind.BUTTON and self.pending is not None:
                self._cooldown[self.pending.rule] = e.at + RULE_COOLDOWN
                self.pending = None
                self.cancelled += 1

            if e.zone is Zone.BATHROOM:
                if self.bathroom_since is None or (
                    self.bathroom_last is not None
                    and e.at - self.bathroom_last > BATHROOM_IDLE_RESET
                ):
                    self.bathroom_since = e.at
                self.bathroom_last = e.at
            elif e.kind is EventKind.MOTION:
                self.bathroom_since = None
                self.bathroom_last = None

    # ---------- периодическая проверка ----------

    def tick(self, now: datetime) -> None:
        """Вызывается устройством раз в минуту."""
        self._resolve_pending(now)

        # Технические тревоги идут родне напрямую: спрашивать человека
        # бессмысленно, если канал мёртв или света нет.
        if self.last_heartbeat is not None and now - self.last_heartbeat > OFFLINE_TIMEOUT:
            self._raise_direct(
                now, Rule.DEVICE_OFFLINE, Severity.ALERT,
                "Устройство не отвечает больше 25 минут",
            )
        if self.on_battery_since is not None and now - self.on_battery_since > POWER_LOST_GRACE:
            self._raise_direct(
                now, Rule.POWER_LOST, Severity.ALERT,
                "Нет электричества больше 20 минут, устройство на аккумуляторе",
            )

        # Пока распорядок не изучен, по нему не судим.
        if not self.baseline.is_trained or self.pending is not None:
            return

        if self._check_bathroom(now):
            return
        if self._check_overslept(now):
            return
        self._check_no_activity(now)

    # ---------- правила ----------

    def _check_no_activity(self, now: datetime) -> bool:
        if self.last_activity is None:
            return False
        gap_min = (now - self.last_activity).total_seconds() / 60.0
        threshold = self.baseline.gap_threshold_min(bucket_of(now))
        if gap_min < threshold:
            return False
        return self._ask(
            now, Rule.NO_ACTIVITY, Severity.URGENT,
            f"Нет движения {gap_min / 60:.1f} ч (обычно в это время не больше "
            f"{threshold / 60:.1f} ч)",
        )

    def _check_overslept(self, now: datetime) -> bool:
        wake = self.baseline.expected_wake_minute()
        if wake is None or self.saw_activity_today:
            return False
        expected = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
            minutes=wake
        )
        if now < expected + OVERSLEEP_GRACE:
            return False
        return self._ask(
            now, Rule.OVERSLEPT, Severity.URGENT,
            f"Не встал: обычно подъём около {int(wake) // 60:02d}:{int(wake) % 60:02d}, "
            f"сейчас {now:%H:%M} и активности не было",
        )

    def _check_bathroom(self, now: datetime) -> bool:
        if self.bathroom_since is None or self.bathroom_last is None:
            return False
        # Движение в санузле должно ПРОДОЛЖАТЬСЯ. Иначе человек просто ушёл.
        if now - self.bathroom_last > BATHROOM_IDLE_RESET:
            self.bathroom_since = None
            self.bathroom_last = None
            return False
        if now - self.bathroom_since < BATHROOM_STUCK:
            return False
        mins = (now - self.bathroom_since).total_seconds() / 60.0
        return self._ask(
            now, Rule.BATHROOM_STUCK_RULE, Severity.URGENT,
            f"В санузле без перерыва {mins:.0f} мин",
        )

    # ---------- механика эскалации ----------

    def _in_cooldown(self, rule: Rule, now: datetime) -> bool:
        until = self._cooldown.get(rule)
        return until is not None and now < until

    def _ask(self, now: datetime, rule: Rule, severity: Severity, text: str) -> bool:
        """Спросить человека. Тревога родне — только если он не ответит."""
        if self._in_cooldown(rule, now):
            return False
        self.pending = _Pending(rule=rule, asked_at=now, severity=severity, text=text)
        self.prompts.append(Prompt(at=now, rule=rule))
        return True

    def _resolve_pending(self, now: datetime) -> None:
        if self.pending is None:
            return
        if now - self.pending.asked_at < CONFIRM_WINDOW:
            return
        p = self.pending
        self.pending = None
        self._cooldown[p.rule] = now + RULE_COOLDOWN
        self.alerts.append(
            FamilyAlert(at=now, rule=p.rule, severity=p.severity,
                        text=f"{p.text}. На вопрос устройства не ответил.")
        )

    def _raise_direct(self, now: datetime, rule: Rule, severity: Severity, text: str) -> None:
        if self._in_cooldown(rule, now):
            return
        self._cooldown[rule] = now + RULE_COOLDOWN
        self.alerts.append(FamilyAlert(at=now, rule=rule, severity=severity, text=text))
