"""Слияние каналов в однозначное состояние постели.

Зачем это нужно: PVDF не видит статический вес, поэтому пропажа дыхания на
плёнке неотличима от ухода с кровати. Тензодатчики под ножками дают статику
напрямую и попутно говорят, сколько людей в постели и сколько они весят.

Ни один канал в одиночку не имеет права поднять ночную тревогу.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .dsp import WindowResult

# Нагрузка на ножки выше этого — в постели кто-то есть. Калибруется пустой
# кроватью при установке: вес каркаса и матраса вычитается.
OCCUPIED_KG = 25.0
# Разница нагрузки между половинами, при которой считаем, что человек один.
# При двух людях обе половины нагружены сопоставимо.
ONE_SIDE_RATIO = 0.35
# Минимальный вес второго человека, чтобы не принять за него одеяло и кота.
SECOND_PERSON_MIN_KG = 25.0


class BedState(enum.StrEnum):
    EMPTY = "пусто"
    ONE = "один"
    TWO = "двое"
    UNKNOWN = "неизвестно"


@dataclass
class LoadReading:
    """Показания тензодатчиков, уже за вычетом веса каркаса и матраса."""

    at: datetime
    left_kg: float
    right_kg: float

    @property
    def total_kg(self) -> float:
        return self.left_kg + self.right_kg


@dataclass
class BedFusion:
    """Состояние постели по статике, динамике и подтверждению из комнаты."""

    state: BedState = BedState.UNKNOWN
    weight_kg: float | None = None
    last_load_at: datetime | None = None
    last_resp_at: datetime | None = None
    # Шевеление на плёнке. Движущееся тело живо, поэтому счётчик пропажи
    # дыхания обязан сбрасываться и им: иначе беспокойный сон, в котором
    # дыхание не вычленяется из-за артефактов, даёт ложную тревогу.
    last_bed_motion_at: datetime | None = None
    last_room_motion_at: datetime | None = None
    occupied_since: datetime | None = None
    load_available: bool = False
    _weight_samples: list[float] = field(default_factory=list)

    def feed_load(self, r: LoadReading) -> None:
        """Статический канал. Он один определяет факт присутствия."""
        self.load_available = True
        self.last_load_at = r.at
        total = r.total_kg
        if total < OCCUPIED_KG:
            self.state = BedState.EMPTY
            self.weight_kg = None
            self.occupied_since = None
            self._weight_samples.clear()
            return

        lighter, heavier = sorted((r.left_kg, r.right_kg))
        both_loaded = (
            heavier > 0 and lighter / heavier >= ONE_SIDE_RATIO
            and lighter >= SECOND_PERSON_MIN_KG
        )
        self.state = BedState.TWO if both_loaded else BedState.ONE
        if self.occupied_since is None:
            self.occupied_since = r.at
        if self.state is BedState.ONE:
            # Вес интересен только когда человек один: иначе он бессмысленен.
            self._weight_samples.append(total)
            if len(self._weight_samples) > 240:
                self._weight_samples.pop(0)
            self.weight_kg = sorted(self._weight_samples)[len(self._weight_samples) // 2]
        else:
            self.weight_kg = None

    def feed_window(self, at: datetime, w: WindowResult) -> None:
        """Динамический канал плёнки."""
        if w.resp_reliable:
            self.last_resp_at = at
        if w.motion:
            self.last_bed_motion_at = at
        if not self.load_available:
            # Тензодатчиков нет (кровать без ножек) — работаем по плёнке, но
            # состояние остаётся менее надёжным, и это видно по UNKNOWN.
            if w.occupants == 2:
                self.state = BedState.TWO
            elif w.occupants == 1:
                self.state = BedState.ONE
            elif not w.motion:
                self.state = BedState.UNKNOWN

    def feed_room_motion(self, at: datetime) -> None:
        """PIR в спальне со стационарного устройства."""
        self.last_room_motion_at = at

    def last_sign_of_life_at(self) -> datetime | None:
        """Последнее доказательство жизни: дыхание ИЛИ шевеление на плёнке."""
        candidates = [t for t in (self.last_resp_at, self.last_bed_motion_at) if t]
        return max(candidates) if candidates else None

    def respiration_missing_for(self, now: datetime) -> timedelta | None:
        last = self.last_sign_of_life_at()
        if last is None:
            return None
        return now - last

    def can_raise_night_alarm(self, now: datetime, resp_gap: timedelta) -> bool:
        """Три условия разом. Любое одно — не повод будить родню.

        1. Человек статически в постели (тензодатчики), и он там один.
        2. Дыхание не регистрируется дольше resp_gap.
        3. В комнате нет движения — то есть он не просто сел и читает.
        """
        if self.state is not BedState.ONE:
            return False
        if not self.load_available:
            # Без статического канала «нет дыхания» означает в том числе
            # «встал с кровати». Тревогу не поднимаем — это была бы ложь.
            return False
        gap = self.respiration_missing_for(now)
        if gap is None or gap < resp_gap:
            return False
        if (
            self.last_room_motion_at is not None
            and now - self.last_room_motion_at < resp_gap
        ):
            return False
        return True
