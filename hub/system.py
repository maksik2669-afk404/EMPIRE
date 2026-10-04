"""Единая система: стационарный блок, постель, воздух и центр решений.

Автономна полностью: все решения принимаются локально, сеть нужна только чтобы
отправить готовое сообщение родне. Пропажа интернета не отключает обнаружение.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from eldercare.baseline import Baseline
from eldercare.events import Event, EventKind, Zone, bucket_of
from morning.dsp import WindowResult
from morning.night import NightRecorder, NightSummary
from morning.presence import BedFusion, BedState, LoadReading

from .air import AirMonitor, AirReading
from .model import DecisionCenter
from .signals import Observation, Signal

# Столько человек имеет на ответ, прежде чем сообщение уйдёт родне.
CONFIRM_WINDOW = timedelta(minutes=10)
# Повторно по тому же поводу не беспокоим.
COOLDOWN = timedelta(hours=6)
# Дыхания нет дольше этого при нагруженной кровати — свидетельство.
RESP_MISSING = timedelta(minutes=3)
# Столько же без дыхания — эскалация по длительности. Ниже этого ночная
# тревога не поднимается, и это честная задержка, а не недоработка.
RESP_MISSING_PROLONGED = timedelta(minutes=10)
BATHROOM_STUCK = timedelta(minutes=40)
OFFLINE_TIMEOUT = timedelta(minutes=25)


class Act(enum.StrEnum):
    ASK_PERSON = "спросить человека"
    FAMILY_ALERT = "сообщить родне"
    PERSON_ADVICE = "совет человеку"


@dataclass
class Decision:
    at: datetime
    act: Act
    text: str
    explanation: str = ""


@dataclass
class HomeSystem:
    baseline: Baseline = field(default_factory=Baseline)
    fusion: BedFusion = field(default_factory=BedFusion)
    air: AirMonitor = field(default_factory=AirMonitor)
    center: DecisionCenter = field(default_factory=DecisionCenter)
    recorder: NightRecorder | None = None

    last_activity: datetime | None = None
    last_heartbeat: datetime | None = None
    bathroom_since: datetime | None = None
    bathroom_last: datetime | None = None
    last_window: WindowResult | None = None

    decisions: list[Decision] = field(default_factory=list)
    _pending_since: datetime | None = None
    _pending_explanation: str = ""
    _cooldown_until: datetime | None = None
    _last_advice: datetime | None = None

    def __post_init__(self) -> None:
        if self.recorder is None:
            self.recorder = NightRecorder(self.fusion)

    # ---------- вход ----------

    def feed_event(self, e: Event) -> None:
        """События стационарного блока: PIR, двери, кнопка, питание."""
        if e.kind is EventKind.HEARTBEAT:
            self.last_heartbeat = e.at
            return
        if not e.is_activity:
            return

        self.last_activity = e.at
        self.last_heartbeat = e.at

        if e.kind is EventKind.BUTTON:
            self.center.observe(Observation(e.at, Signal.BUTTON_OK, ttl_minutes=60.0))
            self._cancel_pending(e.at)
            return

        if e.zone is Zone.FRONT_DOOR:
            self.center.observe(
                Observation(e.at, Signal.FRONT_DOOR_RECENT, ttl_minutes=180.0)
            )
        if e.kind is EventKind.MOTION:
            # Шесть минут, не двадцать: движение доказывает, что человек был
            # жив В ТОТ МОМЕНТ. Долгий срок жизни этого свидетельства глушил
            # ночную тревогу почти всегда.
            self.center.observe(
                Observation(e.at, Signal.ROOM_MOTION_RECENT, str(e.zone or ""), 6.0)
            )
            if e.zone is Zone.BEDROOM:
                # Без этого человек, севший в постели почитать, не блокирует
                # ночную тревогу: PIR его видит, а слияние об этом не знает.
                self.fusion.feed_room_motion(e.at)
        if e.zone is Zone.BATHROOM:
            if self.bathroom_since is None or (
                self.bathroom_last is not None
                and e.at - self.bathroom_last > timedelta(minutes=12)
            ):
                self.bathroom_since = e.at
            self.bathroom_last = e.at
        elif e.kind is EventKind.MOTION:
            self.bathroom_since = None
            self.bathroom_last = None

    def feed_load(self, r: LoadReading) -> None:
        self.fusion.feed_load(r)
        sig = {
            BedState.EMPTY: Signal.BED_EMPTY,
            BedState.ONE: Signal.BED_LOADED,
            BedState.TWO: Signal.TWO_IN_BED,
        }.get(self.fusion.state)
        if sig is not None:
            self.center.observe(Observation(r.at, sig, f"{r.total_kg:.0f} кг", 20.0))

    def feed_window(self, at: datetime, w: WindowResult) -> None:
        self.last_window = w
        assert self.recorder is not None
        if self.recorder.summary is None:
            self.recorder.start_night(at)
        self.recorder.feed(at, w)
        if w.resp_reliable:
            self.last_heartbeat = at

    def feed_air(self, r: AirReading) -> None:
        self.air.feed(r)
        bed_loaded = self.fusion.state in (BedState.ONE, BedState.TWO)
        for o in self.air.observations(r.at, bed_loaded):
            self.center.observe(o)

    # ---------- такт ----------

    def tick(self, now: datetime) -> list[Decision]:
        """Вызывается раз в минуту. Возвращает решения, принятые на этом такте."""
        produced: list[Decision] = []
        self._derive_observations(now)

        produced += self._technical(now)
        produced += self._advice(now)
        produced += self._resolve_pending(now)

        if self._pending_since is None and not self._in_cooldown(now):
            a = self.center.assess(now)
            if a.should_ask:
                self._pending_since = now
                self._pending_explanation = a.explain()
                d = Decision(
                    now, Act.ASK_PERSON,
                    "Нажмите кнопку, если всё хорошо", a.explain(),
                )
                produced.append(d)
        self.decisions += produced
        return produced

    def _derive_observations(self, now: datetime) -> None:
        """Признаки, которые видны только по времени, а не по приходу события."""
        if self.last_activity is not None and self.baseline.is_trained:
            gap_min = (now - self.last_activity).total_seconds() / 60.0
            if gap_min >= self.baseline.gap_threshold_min(bucket_of(now)):
                self.center.observe(Observation(
                    now, Signal.NO_ACTIVITY_BEYOND_BASELINE,
                    f"{gap_min / 60:.1f} ч", ttl_minutes=20.0,
                ))

        if (
            self.bathroom_since is not None
            and self.bathroom_last is not None
            and now - self.bathroom_last <= timedelta(minutes=12)
            and now - self.bathroom_since >= BATHROOM_STUCK
        ):
            mins = (now - self.bathroom_since).total_seconds() / 60.0
            self.center.observe(Observation(
                now, Signal.BATHROOM_CONTINUOUS, f"{mins:.0f} мин", ttl_minutes=20.0,
            ))

        if self.fusion.can_raise_night_alarm(now, RESP_MISSING):
            gap = self.fusion.respiration_missing_for(now)
            detail = f"{gap.total_seconds() / 60:.0f} мин" if gap else ""
            self.center.observe(Observation(
                now, Signal.IN_BED_NO_RESP_NO_MOTION, detail, ttl_minutes=20.0,
            ))
            if gap is not None and gap >= RESP_MISSING_PROLONGED:
                self.center.observe(Observation(
                    now, Signal.IN_BED_NO_RESP_PROLONGED, detail, ttl_minutes=20.0,
                ))

    def _technical(self, now: datetime) -> list[Decision]:
        if self.last_heartbeat is None or now - self.last_heartbeat <= OFFLINE_TIMEOUT:
            return []
        self.center.observe(Observation(now, Signal.DEVICE_OFFLINE, ttl_minutes=60.0))
        if self._in_cooldown(now):
            return []
        self._cooldown_until = now + COOLDOWN
        return [Decision(
            now, Act.FAMILY_ALERT,
            "Устройство не отвечает больше 25 минут — связи с домом нет.",
        )]

    def _advice(self, now: datetime) -> list[Decision]:
        """Польза самому человеку: совет про воздух, не чаще раза в 3 часа."""
        if self._last_advice is not None and now - self._last_advice < timedelta(hours=3):
            return []
        text = self.air.advice_for_person()
        if text is None:
            return []
        self._last_advice = now
        return [Decision(now, Act.PERSON_ADVICE, text)]

    def _resolve_pending(self, now: datetime) -> list[Decision]:
        if self._pending_since is None:
            return []
        if now - self._pending_since < CONFIRM_WINDOW:
            return []
        explanation = self._pending_explanation
        self._pending_since = None
        self._pending_explanation = ""
        self._cooldown_until = now + COOLDOWN
        return [Decision(
            now, Act.FAMILY_ALERT,
            "Устройство задало вопрос и не получило ответа. Стоит позвонить.",
            explanation,
        )]

    def _cancel_pending(self, now: datetime) -> None:
        if self._pending_since is None:
            return
        self._pending_since = None
        self._pending_explanation = ""
        self._cooldown_until = now + COOLDOWN

    def _in_cooldown(self, now: datetime) -> bool:
        return self._cooldown_until is not None and now < self._cooldown_until

    # ---------- утро ----------

    def finish_night(self, now: datetime) -> NightSummary:
        assert self.recorder is not None
        summary = self.recorder.finish(now)
        self.recorder = NightRecorder(self.fusion)
        return summary

    def morning_digest(self, summary: NightSummary, now: datetime, **kw: object) -> str:
        from morning.digest import render

        text = render(summary, **kw)  # type: ignore[arg-type]
        note = self.air.night_air_note(now)
        return f"{text}\n{note}" if note else text
