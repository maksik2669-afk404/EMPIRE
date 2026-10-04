"""Накопление ночи и формирование утренней сводки.

Пульс по одному окну недостоверен: слабый сигнал даёт уверенность на границе
порога. Поэтому ЧСС агрегируется по 15 минут с требованием согласованности
окон — тот же интервал, что и у браслета, и по той же причине.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .dsp import WindowResult
from .presence import BedFusion, BedState

WINDOW = timedelta(minutes=1)
HR_AGGREGATION = timedelta(minutes=15)
# Окон с пульсом внутри блока должно быть не меньше, иначе блок отбрасывается.
HR_MIN_WINDOWS = 5
# Разброс внутри блока больше этого — сигнал неустойчив, блоку не верим.
HR_MAX_SPREAD_BPM = 12.0
# «Дыхание не регистрируется»: формулировка о состоянии датчика, не диагноз.
RESP_MISSING_ALARM = timedelta(minutes=3)
# Встал с кровати дольше этого — считаем отдельным подъёмом, не поворотом.
AWAKENING_MIN = timedelta(minutes=4)


@dataclass
class RespGapEpisode:
    start: datetime
    end: datetime
    corroborated: bool      # подтверждено статикой и отсутствием движения
    # Был ли человек всё это время в постели. Перерыв при пустой кровати —
    # это просто подъём, он уже посчитан в awakenings, и называть его
    # «перерывом в сигнале» значит путать родню.
    in_bed: bool = False

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


@dataclass
class NightSummary:
    date: datetime
    in_bed_from: datetime | None = None
    in_bed_to: datetime | None = None
    time_in_bed: timedelta = timedelta()
    awakenings: int = 0
    resp_bpm_median: float | None = None
    hr_bpm_median: float | None = None
    weight_kg: float | None = None
    two_in_bed_minutes: int = 0
    motion_minutes: int = 0
    resp_gaps: list[RespGapEpisode] = field(default_factory=list)

    @property
    def alarms(self) -> list[RespGapEpisode]:
        """Только подтверждённые эпизоды уходят родне как тревога."""
        return [
            e for e in self.resp_gaps
            if e.corroborated and e.duration >= RESP_MISSING_ALARM
        ]


class NightRecorder:
    """Собирает ночь из минутных окон. Вызывается устройством в реальном времени."""

    def __init__(self, fusion: BedFusion) -> None:
        self.fusion = fusion
        self._resp: list[float] = []
        self._hr_blocks: list[float] = []
        self._block_start: datetime | None = None
        self._block_hr: list[float] = []
        self._out_since: datetime | None = None
        self._gap_start: datetime | None = None
        self._gap_corroborated = False
        self._gap_in_bed = False
        self.summary: NightSummary | None = None

    def start_night(self, at: datetime) -> None:
        self.summary = NightSummary(date=at.replace(hour=0, minute=0, second=0, microsecond=0))

    def feed(self, at: datetime, w: WindowResult) -> None:
        if self.summary is None:
            self.start_night(at)
        s = self.summary
        assert s is not None

        self.fusion.feed_window(at, w)
        in_bed = self.fusion.state in (BedState.ONE, BedState.TWO)

        if in_bed:
            if s.in_bed_from is None:
                s.in_bed_from = at
            s.in_bed_to = at
            s.time_in_bed += WINDOW
            if self._out_since is not None:
                if at - self._out_since >= AWAKENING_MIN:
                    s.awakenings += 1
                self._out_since = None
        elif self._out_since is None and s.in_bed_from is not None:
            self._out_since = at

        if self.fusion.state is BedState.TWO:
            s.two_in_bed_minutes += 1
        if w.motion:
            s.motion_minutes += 1
        if w.resp_reliable and w.resp_bpm is not None:
            self._resp.append(w.resp_bpm)

        self._track_resp_gap(at, w)
        self._track_hr(at, w)

    def _track_resp_gap(self, at: datetime, w: WindowResult) -> None:
        s = self.summary
        assert s is not None
        in_bed_now = self.fusion.state in (BedState.ONE, BedState.TWO)
        if w.resp_reliable:
            if self._gap_start is not None:
                s.resp_gaps.append(
                    RespGapEpisode(
                        self._gap_start, at, self._gap_corroborated, self._gap_in_bed
                    )
                )
                self._gap_start = None
                self._gap_corroborated = False
                self._gap_in_bed = False
            return
        if w.motion:
            # Шевеление само объясняет пропажу дыхания — эпизодом не считаем.
            self._gap_start = None
            self._gap_corroborated = False
            self._gap_in_bed = False
            return
        if self._gap_start is None:
            self._gap_start = at
            self._gap_in_bed = in_bed_now
        elif not in_bed_now:
            self._gap_in_bed = False
        if self.fusion.can_raise_night_alarm(at, RESP_MISSING_ALARM):
            self._gap_corroborated = True

    def _track_hr(self, at: datetime, w: WindowResult) -> None:
        if self._block_start is None:
            self._block_start = at
        if w.hr_bpm is not None:
            self._block_hr.append(w.hr_bpm)
        if at - self._block_start >= HR_AGGREGATION:
            self._close_hr_block()
            self._block_start = at

    def _close_hr_block(self) -> None:
        """Блок принимается, только если окон достаточно и разброс мал."""
        vals = sorted(self._block_hr)
        self._block_hr = []
        if len(vals) < HR_MIN_WINDOWS:
            return
        if vals[-1] - vals[0] > HR_MAX_SPREAD_BPM:
            return
        self._hr_blocks.append(vals[len(vals) // 2])

    def finish(self, at: datetime) -> NightSummary:
        s = self.summary
        assert s is not None
        self._close_hr_block()
        if self._gap_start is not None:
            s.resp_gaps.append(
                RespGapEpisode(self._gap_start, at, self._gap_corroborated, self._gap_in_bed)
            )
        if self._resp:
            r = sorted(self._resp)
            s.resp_bpm_median = r[len(r) // 2]
        if self._hr_blocks:
            h = sorted(self._hr_blocks)
            s.hr_bpm_median = h[len(h) // 2]
        s.weight_kg = self.fusion.weight_kg
        return s
