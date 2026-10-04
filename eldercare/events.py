"""Модель событий устройства. Никакого видео и звука окружения — только факты.

Принцип: устройство не записывает обстановку. Оно фиксирует, что в зоне было
движение и что дверь открылась. Этого достаточно для распорядка и этого
нельзя использовать для слежки за содержанием жизни человека.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class EventKind(enum.IntEnum):
    MOTION = 0           # PIR в зоне
    DOOR = 1             # геркон: холодильник, санузел, входная
    BUTTON = 2           # человек нажал большую кнопку
    VOICE_SENT = 3       # отправил голосовое родне
    POWER_LOST = 4       # перешли на аккумулятор
    POWER_RESTORED = 5
    HEARTBEAT = 6        # устройство живо, канал работает
    # Витальные каналы. Подключаются позже и НЕ входят в путь экстренной
    # тревоги: браслет можно снять, и тревога не должна от него зависеть.
    VITALS_HR = 7        # ЧСС: браслет (день, раз в 15 мин) или матрас (ночь)
    VITALS_RESP = 8      # частота дыхания: пьезоплёнка под матрасом
    BED_PRESENCE = 9     # человек в постели / встал — тоже с матраса


class Zone(enum.StrEnum):
    BEDROOM = "спальня"
    KITCHEN = "кухня"
    BATHROOM = "санузел"
    HALLWAY = "прихожая"
    FRIDGE = "холодильник"
    FRONT_DOOR = "входная"


class VitalsSource(enum.IntEnum):
    WRIST = 0      # браслет: PPG, подвержен артефактам движения
    MATTRESS = 1   # пьезоплёнка: сигнал сильнее, дисциплина не требуется


@dataclass(frozen=True)
class Event:
    at: datetime
    kind: EventKind
    zone: Zone | None = None
    value: float | None = None            # ЧСС в уд/мин, дыхание в вд/мин
    source: VitalsSource | None = None

    @property
    def is_activity(self) -> bool:
        """Признак, что человек жив и двигается.

        Heartbeat устройства сюда не входит: железо может быть живо, когда
        человеку плохо. Витальные каналы тоже не входят — браслет, лежащий
        на комоде, не доказывает, что человек двигается.
        """
        return self.kind in (
            EventKind.MOTION,
            EventKind.DOOR,
            EventKind.BUTTON,
            EventKind.VOICE_SENT,
        )

    @property
    def is_vitals(self) -> bool:
        return self.kind in (EventKind.VITALS_HR, EventKind.VITALS_RESP)


BUCKETS_PER_DAY = 48          # по 30 минут
MINUTES_PER_BUCKET = 30


def bucket_of(at: datetime) -> int:
    return (at.hour * 60 + at.minute) // MINUTES_PER_BUCKET


def is_night_bucket(bucket: int) -> bool:
    """Ночь 23:00-07:00. Ночью нормально не двигаться часами."""
    return bucket >= 46 or bucket < 14


def minutes_of_day(at: datetime) -> int:
    return at.hour * 60 + at.minute
