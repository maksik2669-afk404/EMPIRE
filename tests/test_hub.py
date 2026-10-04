from datetime import datetime, timedelta

import pytest

from eldercare.baseline import Baseline
from eldercare.events import Event, EventKind, Zone
from hub.air import AirMonitor, AirReading
from hub.model import (
    ASK_THRESHOLD,
    ENVIRONMENTAL,
    PRIOR_LOG_ODDS,
    WEIGHTS,
    DecisionCenter,
    max_single_positive_weight,
)
from hub.signals import Observation, Signal
from hub.system import Act, HomeSystem
from morning.dsp import WindowResult
from morning.presence import LoadReading

T0 = datetime(2026, 3, 10, 3, 0)


def _trained() -> Baseline:
    bl = Baseline()
    bl.days_observed = 30
    for b in range(48):
        bl.max_gap_min[b] = 60.0
    bl.wake_minute = 420.0
    return bl


# ---------- инвариант модели ----------

def test_no_single_signal_can_trigger_an_alarm():
    """Самое важное свойство: тревога складывается только из нескольких
    независимых свидетельств. Иначе продукт выключат на первой ошибке."""
    needed = ASK_THRESHOLD - PRIOR_LOG_ODDS
    assert max_single_positive_weight() < needed


def test_every_single_signal_alone_stays_below_threshold():
    for sig, w in WEIGHTS.items():
        if w <= 0:
            continue
        c = DecisionCenter()
        c.observe(Observation(T0, sig, ttl_minutes=60.0))
        assert not c.assess(T0).should_ask, f"{sig} поднимает тревогу в одиночку"


def test_two_signals_cross_the_threshold():
    c = DecisionCenter()
    c.observe(Observation(T0, Signal.IN_BED_NO_RESP_NO_MOTION, "5 мин", 60.0))
    c.observe(Observation(T0, Signal.NO_ACTIVITY_BEYOND_BASELINE, "2.0 ч", 60.0))
    a = c.assess(T0)
    assert a.should_ask
    assert "в постели" in a.explain()


def test_button_press_overrides_accumulated_evidence():
    c = DecisionCenter()
    c.observe(Observation(T0, Signal.IN_BED_NO_RESP_NO_MOTION, "", 60.0))
    c.observe(Observation(T0, Signal.NO_ACTIVITY_BEYOND_BASELINE, "", 60.0))
    assert c.assess(T0).should_ask
    c.observe(Observation(T0, Signal.BUTTON_OK, "", 60.0))
    assert not c.assess(T0).should_ask


def test_room_motion_is_negative_evidence():
    c = DecisionCenter()
    c.observe(Observation(T0, Signal.BATHROOM_CONTINUOUS, "", 60.0))
    c.observe(Observation(T0, Signal.OVERSLEPT, "", 60.0))
    with_motion = DecisionCenter()
    with_motion.observe(Observation(T0, Signal.BATHROOM_CONTINUOUS, "", 60.0))
    with_motion.observe(Observation(T0, Signal.OVERSLEPT, "", 60.0))
    with_motion.observe(Observation(T0, Signal.ROOM_MOTION_RECENT, "", 60.0))
    assert with_motion.assess(T0).log_odds < c.assess(T0).log_odds


def test_stale_observations_drop_out():
    c = DecisionCenter()
    c.observe(Observation(T0, Signal.IN_BED_NO_RESP_NO_MOTION, "", ttl_minutes=10.0))
    c.observe(Observation(T0, Signal.NO_ACTIVITY_BEYOND_BASELINE, "", ttl_minutes=10.0))
    assert c.assess(T0).should_ask
    assert not c.assess(T0 + timedelta(minutes=20)).should_ask


def test_environmental_signals_do_not_affect_the_person_assessment():
    """Холодная квартира — медленный риск, а не признак, что человеку плохо."""
    c = DecisionCenter()
    base = c.assess(T0).log_odds
    for sig in ENVIRONMENTAL:
        c.observe(Observation(T0, sig, "", 180.0))
    assert c.assess(T0).log_odds == pytest.approx(base)
    assert len(c.environmental(T0)) == len(ENVIRONMENTAL)


def test_assessment_explains_itself():
    c = DecisionCenter()
    c.observe(Observation(T0, Signal.IN_BED_NO_RESP_NO_MOTION, "6 мин", 60.0))
    text = c.assess(T0).explain()
    assert "6 мин" in text and "+3.5" in text


# ---------- CO2 как подтверждение дыхания ----------

def _feed_co2(air: AirMonitor, start: datetime, values: list[float], temp: float = 21.0) -> datetime:
    t = start
    for v in values:
        air.feed(AirReading(t, co2_ppm=v, temp_c=temp))
        t += timedelta(minutes=5)
    return t - timedelta(minutes=5)


def test_rising_co2_is_evidence_that_someone_is_breathing():
    air = AirMonitor()
    now = _feed_co2(air, T0, [800, 830, 860, 890, 920, 950])
    obs = air.observations(now, bed_loaded=True)
    assert any(o.signal is Signal.CO2_RISING_IN_BEDROOM for o in obs)


def test_decaying_co2_with_loaded_bed_is_evidence_against():
    air = AirMonitor()
    now = _feed_co2(air, T0, [1200, 1180, 1160, 1140, 1120, 1100])
    obs = air.observations(now, bed_loaded=True)
    assert any(o.signal is Signal.CO2_DECAYING_WHILE_BED_LOADED for o in obs)


def test_open_window_suppresses_all_co2_conclusions():
    """Проветривание даёт ту же картину, что остановка дыхания."""
    air = AirMonitor()
    t = T0
    for v, temp in zip([1200, 1150, 1100, 1050, 1000, 950], [22.0, 21.5, 21.0, 20.5, 20.2, 20.0]):
        air.feed(AirReading(t, co2_ppm=v, temp_c=temp))
        t += timedelta(minutes=5)
    now = t - timedelta(minutes=5)
    assert air.window_probably_open(now)
    obs = air.observations(now, bed_loaded=True)
    assert not any(
        o.signal in (Signal.CO2_DECAYING_WHILE_BED_LOADED, Signal.CO2_FLAT_WHILE_BED_LOADED)
        for o in obs
    )


def test_co2_slope_needs_enough_points():
    air = AirMonitor()
    air.feed(AirReading(T0, co2_ppm=900, temp_c=21.0))
    air.feed(AirReading(T0 + timedelta(minutes=5), co2_ppm=950, temp_c=21.0))
    assert air.co2_slope_ppm_per_hour(T0 + timedelta(minutes=5)) is None


# ---------- температура ----------

def test_sustained_cold_is_reported():
    air = AirMonitor()
    t = T0
    for _ in range(30):
        air.feed(AirReading(t, co2_ppm=600, temp_c=15.0))
        t += timedelta(minutes=5)
    now = t - timedelta(minutes=5)
    obs = air.observations(now, bed_loaded=False)
    assert any(o.signal is Signal.ROOM_VERY_COLD for o in obs)
    assert "холодно" in (air.advice_for_person() or "")


def test_brief_draft_is_not_reported_as_cold():
    air = AirMonitor()
    t = T0
    for temp in [22.0] * 20 + [15.0]:
        air.feed(AirReading(t, co2_ppm=600, temp_c=temp))
        t += timedelta(minutes=5)
    now = t - timedelta(minutes=5)
    obs = air.observations(now, bed_loaded=False)
    assert not any(o.signal is Signal.ROOM_VERY_COLD for o in obs)


def test_heating_failure_detected_by_fast_drop():
    air = AirMonitor()
    t = T0
    for temp in [23.0, 23.0, 22.0, 21.0, 20.0, 19.5]:
        air.feed(AirReading(t, co2_ppm=600, temp_c=temp))
        t += timedelta(minutes=15)
    now = t - timedelta(minutes=15)
    obs = air.observations(now, bed_loaded=False)
    assert any(o.signal is Signal.TEMP_DROPPING_FAST for o in obs)


def test_advice_puts_cold_before_stuffiness():
    air = AirMonitor()
    t = T0
    for _ in range(30):
        air.feed(AirReading(t, co2_ppm=1800.0, temp_c=15.0))
        t += timedelta(minutes=5)
    assert "холодно" in (air.advice_for_person() or "")


# ---------- система целиком ----------

def _good_window() -> WindowResult:
    return WindowResult(True, 1, 15.0, 62.0, False, 40.0, 9.0)


def _no_resp_window() -> WindowResult:
    return WindowResult(True, 1, None, None, False, 1.0, 0.0)


def test_system_asks_then_alerts_when_nobody_answers():
    sys_ = HomeSystem(baseline=_trained())
    t = T0
    sys_.feed_event(Event(t, EventKind.MOTION, Zone.BEDROOM))
    sys_.feed_load(LoadReading(t, 62.0, 1.0))
    sys_.feed_window(t, _good_window())

    # Дыхание пропало и не возвращается. Первые минуты тревоги быть не должно.
    t += timedelta(minutes=1)
    for _ in range(8):
        sys_.feed_load(LoadReading(t, 62.0, 1.0))
        sys_.feed_window(t, _no_resp_window())
        sys_.tick(t)
        t += timedelta(minutes=1)
    assert not any(d.act is Act.ASK_PERSON for d in sys_.decisions), \
        "тревога раньше десяти минут — значит порог проседает"

    # После десяти минут эскалация по длительности перевешивает порог.
    for _ in range(6):
        sys_.feed_load(LoadReading(t, 62.0, 1.0))
        sys_.feed_window(t, _no_resp_window())
        sys_.tick(t)
        t += timedelta(minutes=1)
    assert any(d.act is Act.ASK_PERSON for d in sys_.decisions)

    for _ in range(12):
        sys_.feed_load(LoadReading(t, 62.0, 1.0))
        sys_.feed_window(t, _no_resp_window())
        sys_.tick(t)
        t += timedelta(minutes=1)
    alerts = [d for d in sys_.decisions if d.act is Act.FAMILY_ALERT]
    assert alerts
    assert "в постели" in alerts[0].explanation


def test_system_stands_down_when_person_answers():
    sys_ = HomeSystem(baseline=_trained())
    t = T0
    sys_.feed_event(Event(t, EventKind.MOTION, Zone.BEDROOM))
    sys_.feed_load(LoadReading(t, 62.0, 1.0))
    sys_.feed_window(t, _good_window())
    t += timedelta(minutes=1)
    for _ in range(15):
        sys_.feed_load(LoadReading(t, 62.0, 1.0))
        sys_.feed_window(t, _no_resp_window())
        sys_.tick(t)
        t += timedelta(minutes=1)
    assert any(d.act is Act.ASK_PERSON for d in sys_.decisions)

    sys_.feed_event(Event(t, EventKind.BUTTON))
    for _ in range(15):
        sys_.tick(t)
        t += timedelta(minutes=1)
    assert not [d for d in sys_.decisions if d.act is Act.FAMILY_ALERT]


def test_system_gives_the_person_advice_about_the_air():
    sys_ = HomeSystem(baseline=_trained())
    t = T0
    for _ in range(10):
        sys_.feed_air(AirReading(t, co2_ppm=1800.0, temp_c=21.0))
        t += timedelta(minutes=5)
    advice = [d for d in sys_.tick(t) if d.act is Act.PERSON_ADVICE]
    assert advice and "окно" in advice[0].text


def test_system_reports_offline_without_asking_the_person():
    sys_ = HomeSystem(baseline=_trained())
    sys_.feed_event(Event(T0, EventKind.HEARTBEAT))
    out = sys_.tick(T0 + timedelta(minutes=30))
    assert [d for d in out if d.act is Act.FAMILY_ALERT]
    assert not [d for d in out if d.act is Act.ASK_PERSON]


def test_morning_digest_includes_air_note():
    sys_ = HomeSystem(baseline=_trained())
    t = datetime(2026, 3, 10, 23, 0)
    for _ in range(60):
        sys_.feed_air(AirReading(t, co2_ppm=1700.0, temp_c=21.0))
        sys_.feed_load(LoadReading(t, 62.0, 1.0))
        sys_.feed_window(t, _good_window())
        t += timedelta(minutes=5)
    summary = sys_.finish_night(t)
    text = sys_.morning_digest(summary, t, name="мама")
    assert "Доброе утро" in text
    assert "спёртый" in text or "душнов" in text


def test_sitting_up_in_bed_blocks_the_night_alarm():
    """Человек сел почитать: PIR в спальне его видит, тревоги быть не должно."""
    sys_ = HomeSystem(baseline=_trained())
    t = T0
    sys_.feed_load(LoadReading(t, 62.0, 1.0))
    sys_.feed_window(t, _good_window())
    t += timedelta(minutes=1)
    for i in range(20):
        sys_.feed_load(LoadReading(t, 62.0, 1.0))
        sys_.feed_window(t, _no_resp_window())
        if i % 5 == 0:
            sys_.feed_event(Event(t, EventKind.MOTION, Zone.BEDROOM))
        sys_.tick(t)
        t += timedelta(minutes=1)
    assert not any(d.act is Act.ASK_PERSON for d in sys_.decisions)


def test_co2_decay_shortens_the_path_to_the_threshold():
    """CO2 не украшение: он даёт независимое подтверждение ночью."""
    c = DecisionCenter()
    c.observe(Observation(T0, Signal.IN_BED_NO_RESP_NO_MOTION, "4 мин", 20.0))
    c.observe(Observation(T0, Signal.BED_LOADED, "62 кг", 20.0))
    assert not c.assess(T0).should_ask
    c.observe(Observation(T0, Signal.CO2_DECAYING_WHILE_BED_LOADED, "-60 ppm/ч", 45.0))
    assert c.assess(T0).should_ask


def test_restless_sleep_does_not_raise_an_alarm():
    """Ворочается во сне: дыхание из окон не вычленяется, но человек жив.

    Без сброса счётчика по шевелению на плёнке это была ложная тревога
    каждую беспокойную ночь — то есть смерть продукта.
    """
    sys_ = HomeSystem(baseline=_trained())
    t = T0
    sys_.feed_load(LoadReading(t, 62.0, 1.0))
    sys_.feed_window(t, _good_window())
    t += timedelta(minutes=1)
    moving = WindowResult(True, 1, None, None, True, 30.0, 0.0)
    for i in range(40):
        sys_.feed_load(LoadReading(t, 62.0, 1.0))
        # Каждое третье окно — шевеление, остальные без распознанного дыхания.
        sys_.feed_window(t, moving if i % 3 == 0 else _no_resp_window())
        sys_.tick(t)
        t += timedelta(minutes=1)
    assert not any(d.act is Act.ASK_PERSON for d in sys_.decisions)
