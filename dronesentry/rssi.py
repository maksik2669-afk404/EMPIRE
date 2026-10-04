"""Оценка дистанции по уровню сигнала — для класса B (молчащие FPV).

Честная граница метода: RSSI даёт дистанцию с разбросом в разы, потому что
мощность передатчика цели и её антенна нам неизвестны. Модуль обязан отдавать
не число, а ИНТЕРВАЛ. Любой продукт, который рисует точную дистанцию до FPV
по RSSI, врёт пользователю.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Типичные EIRP передатчиков видео (дБм), по которым строится интервал.
# Нижняя граница — легальные 25 мВт, верхняя — боевые 1.6 Вт с усилителем.
VTX_EIRP_MIN_DBM = 14.0
VTX_EIRP_MAX_DBM = 32.0
VTX_EIRP_TYPICAL_DBM = 27.0  # 500 мВт, самый массовый случай

# Показатель затухания. В воздухе, без переотражений от земли, почти свободное
# пространство. На малой высоте над лесом/застройкой уходит к 2.6.
PATH_LOSS_EXPONENT_AIR = 2.05
PATH_LOSS_EXPONENT_LOW_ALT = 2.6


@dataclass(frozen=True)
class RangeEstimate:
    """Интервальная оценка дистанции. best — медиана, не истина."""

    min_m: float
    best_m: float
    max_m: float

    @property
    def uncertainty_ratio(self) -> float:
        return self.max_m / self.min_m if self.min_m > 0 else math.inf

    def bucket(self) -> str:
        """То, что реально показывается оператору вместо фальшивых метров."""
        if self.best_m < 150:
            return "КРИТИЧНО"
        if self.best_m < 500:
            return "БЛИЗКО"
        if self.best_m < 1500:
            return "СРЕДНЕ"
        return "ДАЛЕКО"


def fspl_db(distance_m: float, freq_mhz: float) -> float:
    """Потери в свободном пространстве."""
    if distance_m <= 0:
        return 0.0
    return 20 * math.log10(distance_m / 1000.0) + 20 * math.log10(freq_mhz) + 32.44


def _range_for_eirp(
    rssi_dbm: float, freq_mhz: float, eirp_dbm: float, rx_gain_dbi: float, exponent: float
) -> float:
    """Обращение лог-дистанционной модели: RSSI = EIRP + Grx - L(d)."""
    budget_db = eirp_dbm + rx_gain_dbi - rssi_dbm
    # L(d) = 32.44 + 20log10(f) + 10*n*log10(d_km)
    ref_db = 32.44 + 20 * math.log10(freq_mhz)
    log_km = (budget_db - ref_db) / (10 * exponent)
    return max(1.0, (10**log_km) * 1000.0)


def estimate_range(
    rssi_dbm: float,
    freq_mhz: float,
    rx_gain_dbi: float = 2.0,
    low_altitude: bool = False,
) -> RangeEstimate:
    """Дистанция до некооперативного источника по измеренному RSSI.

    Интервал строится перебором неизвестной мощности цели, а не статистикой
    измерений: доминирующая неопределённость — именно EIRP передатчика.
    """
    exponent = PATH_LOSS_EXPONENT_LOW_ALT if low_altitude else PATH_LOSS_EXPONENT_AIR
    lo = _range_for_eirp(rssi_dbm, freq_mhz, VTX_EIRP_MIN_DBM, rx_gain_dbi, exponent)
    mid = _range_for_eirp(rssi_dbm, freq_mhz, VTX_EIRP_TYPICAL_DBM, rx_gain_dbi, exponent)
    hi = _range_for_eirp(rssi_dbm, freq_mhz, VTX_EIRP_MAX_DBM, rx_gain_dbi, exponent)
    return RangeEstimate(min_m=lo, best_m=mid, max_m=hi)


def bearing_from_two_antennas(
    rssi_a_dbm: float, rssi_b_dbm: float, boresight_a_deg: float, boresight_b_deg: float
) -> float | None:
    """Грубый пеленг по разнице RSSI двух направленных антенн.

    Работает только пока цель в перекрытии диаграмм. Если разница больше 12 дБ,
    цель вне перекрытия и пеленг не определён — возвращаем None, а не выдумываем.
    """
    delta = rssi_a_dbm - rssi_b_dbm
    if abs(delta) > 12.0:
        return None
    span = (boresight_b_deg - boresight_a_deg + 540.0) % 360.0 - 180.0
    # Линейная интерполяция по разнице; 12 дБ = полный уход к одной антенне.
    frac = 0.5 - (delta / 24.0)
    return (boresight_a_deg + span * frac + 360.0) % 360.0
