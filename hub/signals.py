"""Единая шина наблюдений. Всё, что приходит с датчиков, становится Observation.

Смысл шины: центр принятий решений не знает, какое железо стоит в доме. Он
видит именованные свидетельства. Поэтому отсутствие любого датчика не ломает
систему — просто это свидетельство не приходит.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class Signal(enum.StrEnum):
    """Именованные свидетельства. Имя попадает в объяснение тревоги."""

    # --- стационарный блок ---
    NO_ACTIVITY_BEYOND_BASELINE = "нет движения дольше обычного"
    OVERSLEPT = "не встал к обычному времени"
    BATHROOM_CONTINUOUS = "непрерывно в санузле"
    ROOM_MOTION_RECENT = "движение в комнате"
    FRONT_DOOR_RECENT = "открывалась входная дверь"
    BUTTON_OK = "нажал кнопку «всё хорошо»"
    DEVICE_OFFLINE = "устройство не отвечает"
    POWER_LOST = "нет электричества"

    # --- постель ---
    IN_BED_NO_RESP_NO_MOTION = "в постели, дыхания нет, не двигается"
    IN_BED_NO_RESP_PROLONGED = "в постели без дыхания больше 10 минут"
    BED_LOADED = "кровать нагружена"
    BED_EMPTY = "кровать пуста"
    TWO_IN_BED = "в постели двое"
    WEIGHT_JUMP = "вес изменился скачком"

    # --- воздух ---
    CO2_RISING_IN_BEDROOM = "CO2 в спальне растёт — кто-то дышит"
    CO2_FLAT_WHILE_BED_LOADED = "кровать нагружена, но CO2 не растёт"
    CO2_DECAYING_WHILE_BED_LOADED = "кровать нагружена, но CO2 размывается"
    CO2_HIGH = "душно, CO2 высокий"
    ROOM_COLD = "в квартире холодно"
    ROOM_VERY_COLD = "в квартире опасно холодно"
    ROOM_HOT = "в квартире жарко"
    TEMP_DROPPING_FAST = "температура быстро падает — похоже на отказ отопления"


@dataclass(frozen=True)
class Observation:
    at: datetime
    signal: Signal
    detail: str = ""
    # Насколько свидетельство свежее. Истёкшие в расчёт не входят.
    ttl_minutes: float = 15.0

    def alive_at(self, now: datetime) -> bool:
        return (now - self.at).total_seconds() / 60.0 <= self.ttl_minutes
