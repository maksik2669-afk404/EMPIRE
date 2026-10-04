"""Симулятор суток пожилого человека — для измерения ложных тревог.

Без этого числа продукта нет: заявлять «мало ложных тревог» без замера
означает повторить ошибку академических работ, которые оптимизировали
чувствительность и поэтому не стали продуктами.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

from .events import Event, EventKind, Zone

_JITTER_MIN = 25


def _at(day: datetime, hour: float, rng: random.Random, jitter: int = _JITTER_MIN) -> datetime:
    base = day + timedelta(hours=hour)
    return base + timedelta(minutes=rng.randint(-jitter, jitter))


def _activity(at: datetime, zone: Zone, kind: EventKind = EventKind.MOTION) -> Event:
    return Event(at=at, kind=kind, zone=zone)


def normal_day(day: datetime, rng: random.Random, *, nap: bool | None = None) -> list[Event]:
    """Обычные сутки. Намеренно рваные: человек не робот.

    Включает дневной сон, ночные походы в санузел и редкие выходы из дома —
    всё то, на чём наивные пороги дают ложные тревоги.
    """
    ev: list[Event] = []
    wake = _at(day, 7.0, rng, jitter=40)
    ev.append(_activity(wake, Zone.BEDROOM))
    ev.append(_activity(wake + timedelta(minutes=rng.randint(3, 12)), Zone.BATHROOM))
    ev.append(_activity(wake + timedelta(minutes=rng.randint(15, 35)), Zone.KITCHEN))
    ev.append(
        Event(wake + timedelta(minutes=rng.randint(16, 40)), EventKind.DOOR, Zone.FRIDGE)
    )

    # День: кухня, комната, санузел вперемешку.
    t = wake + timedelta(hours=1)
    end_of_day = day + timedelta(hours=22, minutes=rng.randint(0, 50))
    while t < end_of_day:
        t += timedelta(minutes=rng.randint(20, 75))
        if t >= end_of_day:
            break
        zone = rng.choices(
            [Zone.KITCHEN, Zone.BEDROOM, Zone.BATHROOM, Zone.HALLWAY],
            weights=[4, 4, 2, 1],
        )[0]
        ev.append(_activity(t, zone))
        if zone is Zone.KITCHEN and rng.random() < 0.4:
            ev.append(Event(t + timedelta(minutes=1), EventKind.DOOR, Zone.FRIDGE))

    # Дневной сон 1.5-2.5 ч: главный источник ложных тревог у наивных порогов.
    if nap if nap is not None else rng.random() < 0.6:
        nap_start = _at(day, 14.0, rng, jitter=60)
        nap_len = timedelta(minutes=rng.randint(90, 150))
        ev = [e for e in ev if not (nap_start <= e.at <= nap_start + nap_len)]
        ev.append(_activity(nap_start, Zone.BEDROOM))
        ev.append(_activity(nap_start + nap_len, Zone.BEDROOM))

    # Выход из дома на 2-4 часа: активности в квартире нет вообще.
    if rng.random() < 0.25:
        out = _at(day, 11.0, rng, jitter=70)
        back = out + timedelta(minutes=rng.randint(120, 240))
        ev = [e for e in ev if not (out <= e.at <= back)]
        ev.append(Event(out, EventKind.DOOR, Zone.FRONT_DOOR))
        ev.append(Event(back, EventKind.DOOR, Zone.FRONT_DOOR))
        ev.append(_activity(back + timedelta(minutes=2), Zone.HALLWAY))

    # Ночной санузел 0-2 раза.
    for _ in range(rng.choice([0, 1, 1, 2])):
        ev.append(_activity(_at(day, rng.choice([1.5, 3.0, 4.5]), rng), Zone.BATHROOM))

    ev.append(_activity(end_of_day, Zone.BEDROOM))
    return sorted(ev, key=lambda e: e.at)


def with_heartbeats(events: list[Event], day: datetime) -> list[Event]:
    """Устройство рапортует живость раз в 10 минут независимо от человека."""
    hb = [
        Event(day + timedelta(minutes=10 * i), EventKind.HEARTBEAT)
        for i in range(24 * 6)
    ]
    return sorted(events + hb, key=lambda e: e.at)


# ---------- сценарии ЧП ----------

def scenario_fall_midday(day: datetime, rng: random.Random) -> tuple[list[Event], datetime]:
    """Падение в 11 утра: активность обрывается, кнопку нажать не может."""
    ev = [e for e in normal_day(day, rng, nap=False) if e.at.hour < 11]
    incident = day + timedelta(hours=11)
    return sorted(ev, key=lambda e: e.at), incident


def scenario_stuck_in_bathroom(day: datetime, rng: random.Random) -> tuple[list[Event], datetime]:
    """Упал в санузле: датчик там продолжает видеть движение, выйти не может."""
    ev = [e for e in normal_day(day, rng, nap=False) if e.at.hour < 9]
    incident = day + timedelta(hours=9)
    t = incident
    while t < incident + timedelta(hours=3):
        ev.append(_activity(t, Zone.BATHROOM))
        t += timedelta(minutes=4)
    return sorted(ev, key=lambda e: e.at), incident


def scenario_did_not_wake(day: datetime, rng: random.Random) -> tuple[list[Event], datetime]:
    """Ночное ЧП: утром человек не встал."""
    ev = [e for e in normal_day(day, rng) if e.at.hour < 1]
    incident = day + timedelta(hours=7)
    return sorted(ev, key=lambda e: e.at), incident
