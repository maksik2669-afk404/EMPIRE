"""Модель целей и сырых детекций."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .geo import Fix
from .rssi import RangeEstimate


class TargetClass(enum.IntEnum):
    """Класс цели определяет, что мы о ней вообще способны узнать."""

    COOPERATIVE = 0  # A: транслирует Remote ID / DroneID — есть GPS цели
    EMITTING = 1     # B: молчит по ID, но излучает видео/управление — только RSSI
    SILENT = 2       # C: оптоволокно или полная автономия — радио не видит


class Source(enum.IntEnum):
    REMOTE_ID_WIFI = 0
    REMOTE_ID_BLE = 1
    DJI_DRONEID = 2
    VTX_SWEEP_58 = 3
    VTX_SWEEP_12 = 4
    CTRL_SWEEP_24 = 5


@dataclass
class Detection:
    """Одно измерение одним каналом. Сырьё для фьюжена."""

    t_s: float
    source: Source
    rssi_dbm: float
    freq_mhz: float
    ident: str | None = None       # серийник/UAS ID, если цель кооперативная
    target_fix: Fix | None = None  # позиция цели из пакета Remote ID
    bearing_deg: float | None = None

    @property
    def target_class(self) -> TargetClass:
        if self.source in (Source.REMOTE_ID_WIFI, Source.REMOTE_ID_BLE, Source.DJI_DRONEID):
            return TargetClass.COOPERATIVE
        return TargetClass.EMITTING


@dataclass
class Track:
    """Сопровождаемая цель в системе координат носителя."""

    track_id: int
    target_class: TargetClass
    ident: str | None
    first_seen_s: float
    last_seen_s: float
    hits: int = 1
    # Геометрия относительно носителя
    range_m: float | None = None
    range_estimate: RangeEstimate | None = None
    bearing_deg: float | None = None
    elevation_deg: float | None = None
    closing_mps: float = 0.0
    freqs_mhz: list[float] = field(default_factory=list)
    # Сглаженная дистанция для класса B: RSSI скачет на десятки дБ от
    # ракурса антенны цели, и дифференцировать сырую оценку нельзя.
    range_ema_m: float | None = None

    @property
    def range_is_exact(self) -> bool:
        """True только для класса A. Пилот должен видеть разницу."""
        return self.target_class is TargetClass.COOPERATIVE and self.range_m is not None

    def display_range(self) -> str:
        if self.range_is_exact:
            return f"{self.range_m:.0f} м"
        if self.range_estimate:
            e = self.range_estimate
            return f"{e.min_m:.0f}-{e.max_m:.0f} м ({e.bucket()})"
        return "дистанция неизвестна"
