"""Геодезия для бортового модуля: всё считается ОТ носителя, не от оператора."""
from __future__ import annotations

import math
from dataclasses import dataclass

EARTH_RADIUS_M = 6_371_008.8


@dataclass(frozen=True)
class Fix:
    """Точка в пространстве. lat/lon в градусах, alt — метры над уровнем моря."""

    lat: float
    lon: float
    alt: float = 0.0


def ground_range_m(a: Fix, b: Fix) -> float:
    """Дистанция по поверхности (haversine)."""
    phi1, phi2 = math.radians(a.lat), math.radians(b.lat)
    dphi = phi2 - phi1
    dlam = math.radians(b.lon - a.lon)
    h = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(1.0, h)))


def slant_range_m(a: Fix, b: Fix) -> float:
    """Наклонная дистанция с учётом разницы высот — то, что реально нужно пилоту."""
    g = ground_range_m(a, b)
    return math.hypot(g, b.alt - a.alt)


def bearing_deg(a: Fix, b: Fix) -> float:
    """Истинный пеленг из a на b, 0..360, 0 = север."""
    phi1, phi2 = math.radians(a.lat), math.radians(b.lat)
    dlam = math.radians(b.lon - a.lon)
    y = math.sin(dlam) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlam)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def elevation_deg(a: Fix, b: Fix) -> float:
    """Угол места цели относительно носителя. Положительный — цель выше."""
    g = ground_range_m(a, b)
    if g < 1e-6:
        return 90.0 if b.alt > a.alt else (-90.0 if b.alt < a.alt else 0.0)
    return math.degrees(math.atan2(b.alt - a.alt, g))


def closing_speed_mps(r_prev: float, r_now: float, dt_s: float) -> float:
    """Скорость сближения. Положительная — цель приближается."""
    if dt_s <= 0:
        return 0.0
    return (r_prev - r_now) / dt_s
