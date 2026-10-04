"""Обучение распорядка конкретного человека.

Никаких универсальных порогов: «90 минут без движения» для одного человека
норма, для другого ЧП. Порог обязан вырасти из его собственных двух недель.

Ключевая деталь, в которой легко ошибиться: порог тишины для получаса нужно
учить как «максимальная тишина, НАКРЫВШАЯ этот получас», а не «закончившаяся
в нём». Пока человек спит, в ночных получасах ничего не заканчивается, и при
втором варианте ночь так и не выучивается как время нормальной тишины.

Обучение онлайновое: события подаются по одному, как на устройстве, без
предварительной нарезки истории на сутки.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .events import BUCKETS_PER_DAY, Event, bucket_of, is_night_bucket, minutes_of_day

# Пока базовая линия не обучена, тревоги по распорядку не выдаются вообще.
MIN_DAYS_TO_TRUST = 14
# Скорость забывания. 0.12 даёт полупериод ~6 дней: достаточно быстро, чтобы
# принять новый режим после болезни, достаточно медленно против одного дня.
EMA_ALPHA = 0.12
# Запас над выученным максимумом. Подбирается симуляцией: ниже растёт число
# опросов, выше растёт задержка обнаружения.
GAP_MULT = 1.5
GAP_MARGIN_MIN = 45.0
# Абсолютный потолок: даже у самого малоподвижного человека столько тишины
# подряд — повод спросить. Ночью больше, потому что человек спит.
HARD_CEIL_DAY_MIN = 300.0
HARD_CEIL_NIGHT_MIN = 780.0
# Абсолютный пол: не спрашиваем чаще, чем раз в такую тишину, что бы ни
# показало обучение. Защита от человека с очень дробной активностью.
HARD_FLOOR_MIN = 75.0
# Сколько подряд получасов может накрыть одна тишина, прежде чем считать её
# отсутствием дома. 48 = сутки.
MAX_SPAN_BUCKETS = 48


def _ema(old: float | None, new: float, alpha: float = EMA_ALPHA) -> float:
    return new if old is None else alpha * new + (1.0 - alpha) * old


def buckets_covered(start: datetime, end: datetime) -> list[int]:
    """Получасы, через которые проходит тишина между двумя событиями."""
    out: list[int] = []
    t = start.replace(minute=(start.minute // 30) * 30, second=0, microsecond=0)
    for _ in range(MAX_SPAN_BUCKETS + 1):
        if t > end:
            break
        out.append(bucket_of(t))
        t += timedelta(minutes=30)
    return out


@dataclass
class Baseline:
    days_observed: int = 0
    # Доля дней, когда в этом получасе была активность.
    active_prob: list[float] = field(default_factory=lambda: [0.0] * BUCKETS_PER_DAY)
    # Типичный максимум тишины, накрывавшей этот получас, в минутах.
    max_gap_min: list[float | None] = field(default_factory=lambda: [None] * BUCKETS_PER_DAY)
    # Время первой активности после 04:00, минуты от полуночи.
    wake_minute: float | None = None

    _last_at: datetime | None = None
    _cur_date: date | None = None
    _day_gap: dict[int, float] = field(default_factory=dict)
    _day_seen: set[int] = field(default_factory=set)
    _day_wake: float | None = None

    @property
    def is_trained(self) -> bool:
        return self.days_observed >= MIN_DAYS_TO_TRUST

    def gap_threshold_min(self, bucket: int) -> float:
        """Сколько тишины в этом получасе считать поводом спросить человека."""
        ceil = HARD_CEIL_NIGHT_MIN if is_night_bucket(bucket) else HARD_CEIL_DAY_MIN
        learned = self.max_gap_min[bucket]
        if learned is None:
            return ceil
        return min(ceil, max(HARD_FLOOR_MIN, learned * GAP_MULT + GAP_MARGIN_MIN))

    # ---------- онлайновое обучение ----------

    def observe(self, e: Event) -> None:
        """Подать одно событие. Порядок по времени обязателен."""
        if not e.is_activity:
            return
        if self._cur_date is not None and e.at.date() != self._cur_date:
            self._flush_day()
        self._cur_date = e.at.date()

        if self._last_at is not None:
            gap = (e.at - self._last_at).total_seconds() / 60.0
            if gap > 0:
                for b in buckets_covered(self._last_at, e.at):
                    self._day_gap[b] = max(self._day_gap.get(b, 0.0), gap)
        self._last_at = e.at
        self._day_seen.add(bucket_of(e.at))
        if self._day_wake is None and minutes_of_day(e.at) >= 240:
            self._day_wake = float(minutes_of_day(e.at))

    def _flush_day(self) -> None:
        """Свернуть накопленные за сутки наблюдения в базовую линию."""
        if not self._day_seen:
            return
        for b in range(BUCKETS_PER_DAY):
            self.active_prob[b] = _ema(self.active_prob[b], 1.0 if b in self._day_seen else 0.0)
        for b, gap in self._day_gap.items():
            self.max_gap_min[b] = _ema(self.max_gap_min[b], gap)
        if self._day_wake is not None:
            self.wake_minute = _ema(self.wake_minute, self._day_wake)
        self.days_observed += 1
        self._day_gap = {}
        self._day_seen = set()
        self._day_wake = None

    def learn_day(self, day_events: list[Event]) -> None:
        """Скормить сутки целиком и закрыть их. Удобно для тестов и прогонов."""
        for e in sorted(day_events, key=lambda x: x.at):
            self.observe(e)
        self._flush_day()

    def expected_wake_minute(self) -> float | None:
        return self.wake_minute


def learn_from_history(events: list[Event]) -> Baseline:
    """Собрать базовую линию из сплошной истории событий."""
    bl = Baseline()
    for e in sorted(events, key=lambda x: x.at):
        bl.observe(e)
    bl._flush_day()
    return bl
