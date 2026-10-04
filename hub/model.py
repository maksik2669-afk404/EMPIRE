"""Центр принятий решений: накопление свидетельств в логарифмах шансов.

Почему не обученная модель: каждая тревога обязана быть объяснимой, иначе
родня перестанет ей верить после первой ошибки. Здесь решение всегда можно
распечатать слагаемыми — какое свидетельство сколько добавило.

Почему это всё-таки модель, а не набор if: порог перевешивается только
суммой нескольких независимых свидетельств. Многосигнальное подтверждение
получается свойством арифметики, а не отдельной веткой кода.

Веса заданы руками и документированы. Калибруются на симуляции и на реальных
записях, но никогда не подбираются так, чтобы одно свидетельство в одиночку
переваливало порог.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime

from .signals import Observation, Signal

# Априорная вероятность, что прямо сейчас человеку нужна помощь. Редкое
# событие: примем 1 к 400 на окно проверки. log(p/(1-p)) ~= -6.0.
PRIOR_LOG_ODDS = -6.0
# Порог, после которого устройство СПРАШИВАЕТ человека. До тревоги родне —
# ещё лестница эскалации, как в стационарном блоке.
ASK_THRESHOLD = -1.0

# Веса свидетельств в логарифмах шансов. Ни одно положительное не достигает
# 5.0 = PRIOR_LOG_ODDS - ASK_THRESHOLD, то есть ни одно в одиночку не
# поднимает тревогу. Это проверяется тестом, а не доверием к автору.
WEIGHTS: dict[Signal, float] = {
    # Конъюнкция трёх каналов: плёнка не видит дыхания, тензодатчики говорят
    # что человек в постели, PIR не видит движения в комнате.
    Signal.IN_BED_NO_RESP_NO_MOTION: 3.5,
    # Эскалация по длительности той же конъюнкции. Не независимое свидетельство,
    # а усиление: чем дольше держится, тем меньше вероятность артефакта.
    # Без него ночная тревога по дыханию недостижима, потому что ночью порог
    # тишины велик и второго сильного признака взяться негде.
    Signal.IN_BED_NO_RESP_PROLONGED: 2.0,
    Signal.BATHROOM_CONTINUOUS: 3.0,
    Signal.OVERSLEPT: 2.5,
    Signal.NO_ACTIVITY_BEYOND_BASELINE: 2.0,
    # Медленное, но независимое: полчаса никто не производил CO2 в комнате.
    Signal.CO2_DECAYING_WHILE_BED_LOADED: 2.0,
    Signal.CO2_FLAT_WHILE_BED_LOADED: 1.0,
    Signal.BED_LOADED: 0.3,
    Signal.WEIGHT_JUMP: 0.0,          # медицинский тренд, не экстренный признак
    # Отрицательные: доказательства, что всё в порядке.
    Signal.BUTTON_OK: -4.0,
    Signal.FRONT_DOOR_RECENT: -3.0,
    Signal.ROOM_MOTION_RECENT: -2.5,
    Signal.CO2_RISING_IN_BEDROOM: -1.0,
    Signal.BED_EMPTY: -0.5,
    Signal.TWO_IN_BED: -1.5,          # рядом есть кто-то, кто поможет
}

# Эти свидетельства не участвуют в оценке состояния человека: это отдельные
# тревоги, у каждой своя логика и свой адресат.
TECHNICAL = (Signal.DEVICE_OFFLINE, Signal.POWER_LOST)
# Климат — медленные риски, не экстренные признаки. Спрашивать человека
# «всё хорошо?» из-за сломанного котла бессмысленно, поэтому они идут родне
# отдельным каналом и в оценку состояния не входят.
ENVIRONMENTAL = (
    Signal.ROOM_COLD,
    Signal.ROOM_VERY_COLD,
    Signal.ROOM_HOT,
    Signal.TEMP_DROPPING_FAST,
    Signal.CO2_HIGH,
)
# Свидетельства, которые идут родне сразу, без опроса человека. Сейчас таких
# нет: всё, что касается состояния человека, проходит лестницу эскалации.
BYPASS_LADDER: tuple[Signal, ...] = ()


@dataclass
class Contribution:
    signal: Signal
    weight: float
    detail: str

    def __str__(self) -> str:
        sign = "+" if self.weight >= 0 else ""
        tail = f" ({self.detail})" if self.detail else ""
        return f"{sign}{self.weight:.1f}  {self.signal}{tail}"


@dataclass
class Assessment:
    at: datetime
    log_odds: float
    contributions: list[Contribution] = field(default_factory=list)

    @property
    def probability(self) -> float:
        return 1.0 / (1.0 + math.exp(-self.log_odds))

    @property
    def should_ask(self) -> bool:
        return self.log_odds >= ASK_THRESHOLD

    def explain(self) -> str:
        """То, что уходит родне вместе с тревогой и в журнал."""
        head = f"Оценка {self.probability * 100:.1f}% (log-odds {self.log_odds:+.1f})"
        if not self.contributions:
            return head + "\n  нет свежих свидетельств"
        body = "\n".join(f"  {c}" for c in sorted(
            self.contributions, key=lambda c: -abs(c.weight)
        ))
        return head + "\n" + body


class DecisionCenter:
    """Локальный, автономный. Ни одного обращения к сети для принятия решения."""

    def __init__(self, weights: dict[Signal, float] | None = None) -> None:
        self.weights = dict(WEIGHTS if weights is None else weights)
        self._obs: list[Observation] = []

    def observe(self, o: Observation) -> None:
        # Одно свидетельство одного вида — держим самое свежее.
        self._obs = [x for x in self._obs if x.signal is not o.signal]
        self._obs.append(o)

    def active(self, now: datetime) -> list[Observation]:
        self._obs = [o for o in self._obs if o.alive_at(now)]
        return list(self._obs)

    def assess(self, now: datetime) -> Assessment:
        total = PRIOR_LOG_ODDS
        contribs = [Contribution(Signal.NO_ACTIVITY_BEYOND_BASELINE, 0.0, "")][:0]
        for o in self.active(now):
            if o.signal in TECHNICAL or o.signal in ENVIRONMENTAL:
                continue
            w = self.weights.get(o.signal, 0.0)
            if w == 0.0:
                continue
            total += w
            contribs.append(Contribution(o.signal, w, o.detail))
        return Assessment(at=now, log_odds=total, contributions=contribs)

    def technical_alarms(self, now: datetime) -> list[Observation]:
        return [o for o in self.active(now) if o.signal in TECHNICAL]

    def environmental(self, now: datetime) -> list[Observation]:
        return [o for o in self.active(now) if o.signal in ENVIRONMENTAL]

    def bypass_alarms(self, now: datetime) -> list[Observation]:
        """Тревоги, которые идут родне сразу, без опроса человека."""
        return [o for o in self.active(now) if o.signal in BYPASS_LADDER]


def max_single_positive_weight(weights: dict[Signal, float] | None = None) -> float:
    w = WEIGHTS if weights is None else weights
    return max((v for v in w.values() if v > 0), default=0.0)
