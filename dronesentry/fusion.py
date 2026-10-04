"""Фьюжен детекций в треки и оценка угрозы.

Вся геометрия — относительно носителя (own_fix), который обновляется бортовым
GPS модуля. Позиция оператора в расчётах не участвует вообще.
"""
from __future__ import annotations

from dataclasses import dataclass

from .geo import Fix, bearing_deg, closing_speed_mps, elevation_deg, slant_range_m
from .rssi import estimate_range
from .targets import Detection, Source, TargetClass, Track

# Цель считается потерянной, если молчит дольше этого. Remote ID шлётся ~1 Гц,
# свип по 5.8 проходит полный круг за ~2 с — 8 с даёт запас на пропуски.
TRACK_TIMEOUT_S = 8.0
# Класс B ассоциируем по частоте: каналы FPV стоят с шагом 5-19 МГц.
FREQ_MATCH_MHZ = 9.0


# Время до контакта, при котором пилот ещё способен увести носитель.
# 10 с не хватает: нужно заметить алерт, опознать направление и дать манёвр.
TTI_CRITICAL_S = 20.0
TTI_WARN_S = 45.0
RANGE_CRITICAL_M = 150.0
RANGE_WARN_M = 600.0
# Ниже этой скорости сближения счётчик времени до контакта шумит.
MIN_CLOSING_MPS = 0.5
# Физический предел: FPV-перехватчик ~50 м/с плюс собственная скорость
# Mavic ~20 м/с. Всё, что выше, — артефакт измерения, а не цель.
MAX_CLOSING_MPS = 70.0
# Сглаживание RSSI-дистанции. 0.35 даёт константу времени ~2 с при 1 Гц:
# достаточно быстро для реакции, достаточно медленно против выбросов.
RANGE_EMA_ALPHA = 0.35


@dataclass
class Alert:
    track: Track
    level: str      # INFO | WARN | CRITICAL
    reason: str
    tti_s: float = float("inf")   # время до контакта, с
    range_m: float | None = None


class Tracker:
    def __init__(self, low_altitude: bool = False, rx_gain_dbi: float = 2.0) -> None:
        self.tracks: dict[int, Track] = {}
        self.own_fix: Fix | None = None
        self._next_id = 1
        self._low_altitude = low_altitude
        self._rx_gain = rx_gain_dbi

    def set_own_fix(self, fix: Fix) -> None:
        """Позиция носителя с бортового GPS модуля."""
        self.own_fix = fix

    def _associate(self, det: Detection) -> Track | None:
        if det.ident:
            for tr in self.tracks.values():
                if tr.ident == det.ident:
                    return tr
            return None
        # Некооперативная цель: та же частота и тот же класс.
        for tr in self.tracks.values():
            if tr.target_class is not TargetClass.EMITTING:
                continue
            if any(abs(f - det.freq_mhz) <= FREQ_MATCH_MHZ for f in tr.freqs_mhz):
                return tr
        return None

    def update(self, det: Detection) -> Track:
        tr = self._associate(det)
        if tr is None:
            tr = Track(
                track_id=self._next_id,
                target_class=det.target_class,
                ident=det.ident,
                first_seen_s=det.t_s,
                last_seen_s=det.t_s,
            )
            self._next_id += 1
            self.tracks[tr.track_id] = tr
        else:
            tr.hits += 1

        prev_range = tr.range_m if tr.range_is_exact else tr.range_ema_m
        prev_t = tr.last_seen_s
        tr.last_seen_s = det.t_s
        if det.freq_mhz and not any(abs(f - det.freq_mhz) <= 1.0 for f in tr.freqs_mhz):
            tr.freqs_mhz.append(det.freq_mhz)

        if det.target_fix is not None and self.own_fix is not None:
            # Класс A: дистанция из GPS цели — точная.
            tr.range_m = slant_range_m(self.own_fix, det.target_fix)
            tr.bearing_deg = bearing_deg(self.own_fix, det.target_fix)
            tr.elevation_deg = elevation_deg(self.own_fix, det.target_fix)
            tr.range_estimate = None
            new_range = tr.range_m
        else:
            # Класс B: только интервал по RSSI.
            tr.range_estimate = estimate_range(
                det.rssi_dbm,
                det.freq_mhz,
                rx_gain_dbi=self._rx_gain,
                low_altitude=self._low_altitude,
            )
            tr.range_m = None
            if det.bearing_deg is not None:
                tr.bearing_deg = det.bearing_deg
            raw = tr.range_estimate.best_m
            tr.range_ema_m = (
                raw
                if tr.range_ema_m is None
                else RANGE_EMA_ALPHA * raw + (1.0 - RANGE_EMA_ALPHA) * tr.range_ema_m
            )
            new_range = tr.range_ema_m

        if prev_range is not None and new_range is not None:
            raw_closing = closing_speed_mps(prev_range, new_range, det.t_s - prev_t)
            tr.closing_mps = max(-MAX_CLOSING_MPS, min(MAX_CLOSING_MPS, raw_closing))
        return tr

    def prune(self, now_s: float) -> list[int]:
        dead = [i for i, t in self.tracks.items() if now_s - t.last_seen_s > TRACK_TIMEOUT_S]
        for i in dead:
            del self.tracks[i]
        return dead

    def alerts(self) -> list[Alert]:
        """Приоритет — по времени до сближения, а не по дистанции.

        Дрон на 800 м, идущий на нас 25 м/с, опаснее висящего на 200 м.
        """
        out: list[Alert] = []
        for tr in self.tracks.values():
            r = tr.range_m if tr.range_is_exact else tr.range_ema_m
            if r is None:
                out.append(Alert(tr, "INFO", "цель обнаружена, дистанция неизвестна"))
                continue
            tti = r / tr.closing_mps if tr.closing_mps > MIN_CLOSING_MPS else float("inf")
            if r < RANGE_CRITICAL_M or tti < TTI_CRITICAL_S:
                level = "CRITICAL"
            elif r < RANGE_WARN_M or tti < TTI_WARN_S:
                level = "WARN"
            else:
                level = "INFO"
            reason = tr.display_range()
            if tti < float("inf"):
                # Для класса B и скорость, и время до контакта — оценка по RSSI.
                hedge = "~" if not tr.range_is_exact else ""
                reason += (
                    f", сближение {hedge}{tr.closing_mps:.0f} м/с"
                    f", контакт через {hedge}{tti:.0f} с"
                )
            out.append(Alert(tr, level, reason, tti_s=tti, range_m=r))

        order = {"CRITICAL": 0, "WARN": 1, "INFO": 2}
        # Внутри уровня — сначала то, до чего меньше времени, и лишь потом
        # то, что просто ближе. Иначе висящая рядом цель маскирует атакующую.
        return sorted(
            out,
            key=lambda a: (
                order[a.level],
                a.tti_s,
                a.range_m if a.range_m is not None else float("inf"),
                a.track.track_id,
            ),
        )
