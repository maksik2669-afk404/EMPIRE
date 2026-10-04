"""CO2 в спальне как независимое подтверждение дыхания.

Идея: дышащий человек производит CO2, и в закрытой спальне это видно как
устойчивый рост. Если тело перестало его вырабатывать, рост прекращается и
концентрация начинает размываться воздухообменом.

ФИЗИКА, КОТОРУЮ НЕЛЬЗЯ ИГНОРИРОВАТЬ: размывание медленное. Постоянная времени
комнаты — это 1/кратность воздухообмена, обычно от 30 минут до нескольких
часов. Поэтому CO2 НЕ может подтвердить острый эпизод в три минуты. Он
отвечает на другой вопрос: «дышал ли вообще кто-нибудь в этой комнате
последние полчаса». Это медленное, но по-настоящему независимое свидетельство,
и вес ему назначен соответственно.

Главный конфаундер — открытое окно: даёт ту же картину, что остановка дыхания.
Отсекается по падению температуры.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .signals import Observation, Signal

# Уличный воздух ~420 ppm. Выше 1000 душно, выше 1600 [Вероятно] портится сон.
CO2_STUFFY_PPM = 1000.0
CO2_BAD_PPM = 1600.0

# Спящий взрослый выдыхает ~15 л CO2 в час. В закрытой спальне 25-35 м3 это
# даёт рост заметно больше этого порога. Ниже — либо окно открыто, либо никто
# не дышит.
CO2_BREATHING_SLOPE_PPM_H = 60.0
# Падение быстрее этого при нагруженной кровати — в комнате никто не производит
# CO2. Окно наблюдения ниже, поэтому свидетельство приходит с задержкой ~30 мин.
CO2_DECAY_SLOPE_PPM_H = -40.0
# Окно оценки наклона. Короче — шум датчика (SCD41 даёт +-(50 ppm + 5%)).
CO2_SLOPE_WINDOW = timedelta(minutes=30)
MIN_SLOPE_POINTS = 5

# Температура упала сильнее этого за окно наблюдения — открыли окно, и любые
# выводы по CO2 о дыхании недействительны.
WINDOW_OPEN_TEMP_DROP_C = 1.5

# Температура. ВОЗ держит 18 C как минимум для жилья; ниже 16 C [Вероятно]
# растёт риск сердечно-сосудистых событий. Пожилые недотапливают из экономии
# и не чувствуют холода — терморегуляция с возрастом слабеет.
TEMP_COLD_C = 18.0
TEMP_VERY_COLD_C = 16.0
# Жара убивает пожилых не хуже холода. В спальне выше 28 C спать вредно.
TEMP_HOT_C = 28.0
# Падение на столько за два часа зимой — похоже на отказ отопления.
TEMP_FAILURE_DROP_C = 3.0
TEMP_FAILURE_WINDOW = timedelta(hours=2)
# Холод должен держаться, иначе сработаем на открытую форточку.
TEMP_SUSTAIN = timedelta(hours=2)


@dataclass
class AirReading:
    at: datetime
    co2_ppm: float | None = None
    temp_c: float | None = None
    humidity_pct: float | None = None


@dataclass
class AirMonitor:
    history: list[AirReading] = field(default_factory=list)

    def feed(self, r: AirReading) -> None:
        self.history.append(r)
        cutoff = r.at - timedelta(hours=12)
        self.history = [h for h in self.history if h.at >= cutoff]

    def _window(self, now: datetime) -> list[AirReading]:
        return [h for h in self.history if now - h.at <= CO2_SLOPE_WINDOW]

    def co2_slope_ppm_per_hour(self, now: datetime) -> float | None:
        """Наклон по методу наименьших квадратов за последние полчаса."""
        pts = [h for h in self._window(now) if h.co2_ppm is not None]
        if len(pts) < MIN_SLOPE_POINTS:
            return None
        t0 = pts[0].at
        xs = [(p.at - t0).total_seconds() / 3600.0 for p in pts]
        ys = [p.co2_ppm for p in pts]
        n = len(xs)
        mx, my = sum(xs) / n, sum(ys) / n
        den = sum((x - mx) ** 2 for x in xs)
        if den <= 0:
            return None
        return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den

    def window_probably_open(self, now: datetime) -> bool:
        """Резкое похолодание = проветривание. Выводы по CO2 отменяются."""
        temps = [h.temp_c for h in self._window(now) if h.temp_c is not None]
        if len(temps) < MIN_SLOPE_POINTS:
            return False
        return (max(temps) - temps[-1]) >= WINDOW_OPEN_TEMP_DROP_C

    def latest(self) -> AirReading | None:
        return self.history[-1] if self.history else None

    def observations(self, now: datetime, bed_loaded: bool) -> list[Observation]:
        """Свидетельства для центра принятий решений."""
        out: list[Observation] = []
        cur = self.latest()
        if cur is None:
            return out

        if cur.co2_ppm is not None and cur.co2_ppm >= CO2_STUFFY_PPM:
            out.append(Observation(
                now, Signal.CO2_HIGH, f"{cur.co2_ppm:.0f} ppm", ttl_minutes=60.0
            ))

        out += self._temperature_observations(now)

        slope = self.co2_slope_ppm_per_hour(now)
        if slope is None or self.window_probably_open(now):
            return out

        if slope >= CO2_BREATHING_SLOPE_PPM_H:
            out.append(Observation(
                now, Signal.CO2_RISING_IN_BEDROOM, f"+{slope:.0f} ppm/ч",
                ttl_minutes=45.0,
            ))
        elif bed_loaded and slope <= CO2_DECAY_SLOPE_PPM_H:
            # Кровать нагружена, но CO2 размывается — в комнате никто не
            # производит его последние полчаса. Самое сильное из медленных
            # свидетельств, но именно медленное: острый эпизод так не поймать.
            out.append(Observation(
                now, Signal.CO2_DECAYING_WHILE_BED_LOADED, f"{slope:.0f} ppm/ч",
                ttl_minutes=45.0,
            ))
        elif bed_loaded and slope < CO2_BREATHING_SLOPE_PPM_H / 3.0:
            out.append(Observation(
                now, Signal.CO2_FLAT_WHILE_BED_LOADED, f"{slope:+.0f} ppm/ч",
                ttl_minutes=45.0,
            ))
        return out

    def _temperature_observations(self, now: datetime) -> list[Observation]:
        """Климат. Медленные риски, отдельный канал, не экстренные признаки."""
        out: list[Observation] = []
        cur = self.latest()
        if cur is None or cur.temp_c is None:
            return out

        sustained = [
            h.temp_c for h in self.history
            if h.temp_c is not None and now - h.at <= TEMP_SUSTAIN
        ]
        if len(sustained) >= MIN_SLOPE_POINTS and max(sustained) < TEMP_VERY_COLD_C:
            out.append(Observation(
                now, Signal.ROOM_VERY_COLD,
                f"{cur.temp_c:.0f} C дольше двух часов", ttl_minutes=180.0,
            ))
        elif len(sustained) >= MIN_SLOPE_POINTS and max(sustained) < TEMP_COLD_C:
            out.append(Observation(
                now, Signal.ROOM_COLD, f"{cur.temp_c:.0f} C", ttl_minutes=180.0
            ))
        elif cur.temp_c >= TEMP_HOT_C:
            out.append(Observation(
                now, Signal.ROOM_HOT, f"{cur.temp_c:.0f} C", ttl_minutes=180.0
            ))

        window = [
            h.temp_c for h in self.history
            if h.temp_c is not None and now - h.at <= TEMP_FAILURE_WINDOW
        ]
        if len(window) >= MIN_SLOPE_POINTS and (max(window) - window[-1]) >= TEMP_FAILURE_DROP_C:
            out.append(Observation(
                now, Signal.TEMP_DROPPING_FAST,
                f"{max(window):.0f} -> {window[-1]:.0f} C за два часа", ttl_minutes=180.0,
            ))
        return out

    def advice_for_person(self) -> str | None:
        """Совет самому человеку, а не родне. Это его польза от системы."""
        cur = self.latest()
        if cur is None:
            return None
        # Холод опаснее духоты, поэтому идёт первым.
        if cur.temp_c is not None and cur.temp_c < TEMP_VERY_COLD_C:
            return "В квартире холодно. Наденьте тёплое и добавьте отопление."
        if cur.temp_c is not None and cur.temp_c >= TEMP_HOT_C:
            return "В комнате жарко. Выпейте воды и зашторьте окно."
        if cur.co2_ppm is None:
            return None
        if cur.co2_ppm >= CO2_BAD_PPM:
            return "В комнате душно. Откройте окно на десять минут — будете лучше спать."
        if cur.co2_ppm >= CO2_STUFFY_PPM:
            return "Воздух спёртый. Хорошо бы приоткрыть окно."
        return None

    def night_air_note(self, now: datetime) -> str | None:
        """Строка для утренней сводки родне."""
        night = [
            h for h in self.history
            if h.co2_ppm is not None and now - h.at <= timedelta(hours=10)
        ]
        if len(night) < 5:
            return None
        vals = sorted(h.co2_ppm for h in night)
        median = vals[len(vals) // 2]
        if median >= CO2_BAD_PPM:
            return (
                f"Воздух в спальне был спёртый всю ночь ({median:.0f} ppm). "
                f"Это портит сон — стоит договориться о приоткрытом окне."
            )
        if median >= CO2_STUFFY_PPM:
            return f"Воздух в спальне душноват ({median:.0f} ppm)."
        return None
