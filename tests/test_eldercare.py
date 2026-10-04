import random
from datetime import datetime, timedelta

import pytest

from eldercare.baseline import MIN_DAYS_TO_TRUST, Baseline, buckets_covered, learn_from_history
from eldercare.detector import CONFIRM_WINDOW, Detector, Rule, Severity
from eldercare.evaluate import evaluate
from eldercare.events import Event, EventKind, Zone, bucket_of, is_night_bucket
from eldercare.simulator import normal_day, with_heartbeats

DAY = datetime(2026, 1, 1)


def _ev(hour: float, zone=Zone.KITCHEN, kind=EventKind.MOTION, day=DAY):
    return Event(day + timedelta(hours=hour), kind, zone)


# ---------- базовая линия ----------

def test_night_buckets_classified_correctly():
    assert is_night_bucket(bucket_of(DAY + timedelta(hours=3)))
    assert not is_night_bucket(bucket_of(DAY + timedelta(hours=12)))


def test_buckets_covered_spans_the_whole_silence():
    covered = buckets_covered(DAY + timedelta(hours=1), DAY + timedelta(hours=4))
    assert bucket_of(DAY + timedelta(hours=2)) in covered
    assert bucket_of(DAY + timedelta(hours=3, minutes=30)) in covered


def test_silence_is_learned_for_buckets_it_passes_through_not_only_where_it_ends():
    """Этот баг давал тревогу в 04:10: ночные получасы не узнавали, что
    тишина в них нормальна, потому что в них ничего не заканчивалось."""
    bl = Baseline()
    bl.learn_day([_ev(23.0, Zone.BEDROOM), _ev(7.0 + 24, Zone.BEDROOM)][:1] + [_ev(0.5, Zone.BATHROOM), _ev(7.0)])
    mid_night = bucket_of(DAY + timedelta(hours=4))
    assert bl.max_gap_min[mid_night] is not None
    assert bl.max_gap_min[mid_night] > 180


def test_baseline_is_not_trusted_before_two_weeks():
    bl = Baseline()
    rng = random.Random(3)
    day = DAY
    for _ in range(MIN_DAYS_TO_TRUST - 1):
        bl.learn_day(normal_day(day, rng))
        day += timedelta(days=1)
    assert not bl.is_trained
    bl.learn_day(normal_day(day, rng))
    assert bl.is_trained


def test_empty_day_is_not_learned():
    bl = Baseline()
    bl.learn_day([])
    assert bl.days_observed == 0


def test_wake_time_is_learned_from_activity_after_four_am():
    bl = Baseline()
    for i in range(5):
        day = DAY + timedelta(days=i)
        bl.learn_day([_ev(2.0, Zone.BATHROOM, day=day), _ev(7.0, day=day), _ev(9.0, day=day)])
    assert bl.expected_wake_minute() == pytest.approx(420.0, abs=20.0)


def test_learn_from_history_matches_day_by_day_learning():
    rng = random.Random(11)
    events: list[Event] = []
    day = DAY
    for _ in range(5):
        events += normal_day(day, rng)
        day += timedelta(days=1)
    assert learn_from_history(events).days_observed == 5


# ---------- детектор ----------

def _trained_baseline(seed=5, days=21) -> Baseline:
    bl = Baseline()
    rng = random.Random(seed)
    day = DAY
    for _ in range(days):
        bl.learn_day(normal_day(day, rng))
        day += timedelta(days=1)
    return bl



def _tick_with_heartbeats(det: Detector, start: datetime, minutes: int):
    """Такты с живым каналом: иначе детектор законно рапортует «офлайн»."""
    t = start
    for i in range(minutes):
        if i % 10 == 0:
            det.feed(Event(t, EventKind.HEARTBEAT))
        det.tick(t)
        t += timedelta(minutes=1)
    return t


def test_untrained_detector_stays_silent():
    det = Detector(baseline=Baseline())
    det.feed(_ev(8.0))
    _tick_with_heartbeats(det, DAY + timedelta(hours=8), 600)
    assert det.prompts == [] and det.alerts == []


def test_person_is_asked_before_family_is_alerted():
    det = Detector(baseline=_trained_baseline())
    det.feed(_ev(9.0))
    _tick_with_heartbeats(det, DAY + timedelta(hours=9), 600)
    assert det.prompts, "человека обязаны спросить"
    assert det.prompts[0].at < det.alerts[0].at


def test_button_press_cancels_the_escalation():
    det = Detector(baseline=_trained_baseline())
    det.feed(_ev(9.0))
    t = DAY + timedelta(hours=9)
    i = 0
    while not det.prompts:
        if i % 10 == 0:
            det.feed(Event(t, EventKind.HEARTBEAT))
        det.tick(t)
        t += timedelta(minutes=1)
        i += 1
    det.feed(Event(t, EventKind.BUTTON))
    _tick_with_heartbeats(det, t, 30)
    assert det.alerts == []
    assert det.cancelled == 1


def test_family_is_alerted_only_after_the_confirm_window():
    det = Detector(baseline=_trained_baseline())
    det.feed(_ev(9.0))
    t = DAY + timedelta(hours=9)
    i = 0
    while not det.prompts:
        if i % 10 == 0:
            det.feed(Event(t, EventKind.HEARTBEAT))
        det.tick(t)
        t += timedelta(minutes=1)
        i += 1
    asked = det.prompts[0].at
    det.feed(Event(asked, EventKind.HEARTBEAT))
    det.tick(asked + CONFIRM_WINDOW - timedelta(minutes=1))
    assert det.alerts == []
    det.tick(asked + CONFIRM_WINDOW)
    assert len([a for a in det.alerts if a.rule is Rule.NO_ACTIVITY]) == 1
    assert det.alerts[0].severity >= Severity.ALERT


def test_single_night_bathroom_visit_is_not_stuck():
    """Человек сходил в туалет в 1:33 и тихо ушёл спать. Раньше это давало
    тревогу «застрял» через 40 минут."""
    det = Detector(baseline=_trained_baseline())
    det.feed(Event(DAY + timedelta(hours=1, minutes=33), EventKind.MOTION, Zone.BATHROOM))
    t = DAY + timedelta(hours=1, minutes=34)
    for _ in range(120):
        det.tick(t)
        t += timedelta(minutes=1)
    assert not [p for p in det.prompts if p.rule is Rule.BATHROOM_STUCK_RULE]


def test_continuous_bathroom_motion_is_reported():
    det = Detector(baseline=_trained_baseline())
    t = DAY + timedelta(hours=9)
    for _ in range(50):
        det.feed(Event(t, EventKind.MOTION, Zone.BATHROOM))
        det.tick(t)
        t += timedelta(minutes=1)
    assert [p for p in det.prompts if p.rule is Rule.BATHROOM_STUCK_RULE]


def test_device_offline_goes_straight_to_family():
    det = Detector(baseline=_trained_baseline())
    det.feed(Event(DAY + timedelta(hours=9), EventKind.HEARTBEAT))
    det.tick(DAY + timedelta(hours=9, minutes=30))
    offline = [a for a in det.alerts if a.rule is Rule.DEVICE_OFFLINE]
    assert offline
    assert not [p for p in det.prompts if p.rule is Rule.DEVICE_OFFLINE]


def test_power_loss_is_reported_after_the_grace_period():
    det = Detector(baseline=_trained_baseline())
    t = DAY + timedelta(hours=9)
    det.feed(Event(t, EventKind.MOTION, Zone.KITCHEN))
    det.feed(Event(t, EventKind.POWER_LOST))
    det.tick(t + timedelta(minutes=10))
    assert not [a for a in det.alerts if a.rule is Rule.POWER_LOST]
    det.tick(t + timedelta(minutes=25))
    assert [a for a in det.alerts if a.rule is Rule.POWER_LOST]


def test_cooldown_prevents_repeated_nagging():
    det = Detector(baseline=_trained_baseline())
    det.feed(_ev(9.0))
    _tick_with_heartbeats(det, DAY + timedelta(hours=9), 900)
    no_activity = [a for a in det.alerts if a.rule is Rule.NO_ACTIVITY]
    assert len(no_activity) <= 3


def test_heartbeats_alone_never_count_as_activity():
    """Железо может быть живо, когда человеку плохо."""
    det = Detector(baseline=_trained_baseline())
    det.feed(_ev(9.0))
    t = DAY + timedelta(hours=9)
    for i in range(600):
        if i % 10 == 0:
            det.feed(Event(t, EventKind.HEARTBEAT))
        det.tick(t)
        t += timedelta(minutes=1)
    assert det.prompts


# ---------- интегральная оценка ----------

def test_measured_false_alarm_rate_stays_at_zero():
    """Главное обещание продукта, проверяемое числом, а не словами."""
    r = evaluate(seed=7, normal_days=45, incident_runs=10)
    assert r["false_alerts"] == 0
    assert r["prompts_on_normal_days"] / r["normal_days"] < 1.0


def test_all_incident_scenarios_are_detected():
    r = evaluate(seed=7, normal_days=20, incident_runs=10)
    for name, hits in r["detected"].items():
        assert hits == r["incident_runs"], f"сценарий «{name}» пропущен"


def test_simulated_day_contains_the_hard_cases():
    """Симулятор обязан содержать именно то, на чём ломаются наивные пороги."""
    rng = random.Random(2)
    days = [normal_day(DAY + timedelta(days=i), rng) for i in range(40)]
    assert any(
        any(e.zone is Zone.FRONT_DOOR for e in d) for d in days
    ), "нет дней с выходом из дома"
    assert any(
        any(e.zone is Zone.BATHROOM and e.at.hour < 6 for e in d) for d in days
    ), "нет ночных визитов в санузел"


def test_heartbeats_are_injected_across_the_whole_day():
    events = with_heartbeats(normal_day(DAY, random.Random(1)), DAY)
    hb = [e for e in events if e.kind is EventKind.HEARTBEAT]
    assert len(hb) == 144
