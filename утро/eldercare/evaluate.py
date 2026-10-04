"""Измерение движка: ложные тревоги на нормальных днях и обнаружение ЧП.

    python3 -m eldercare.evaluate
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta

from .baseline import Baseline
from .detector import Detector, Severity
from .events import Event, EventKind
from .simulator import (
    normal_day,
    scenario_did_not_wake,
    scenario_fall_midday,
    scenario_stuck_in_bathroom,
    with_heartbeats,
)

TICK = timedelta(minutes=1)
START = datetime(2026, 1, 1)


def _run(detector: Detector, events: list[Event], day: datetime, hours: float = 24.0) -> None:
    """Прогон суток с минутным тиком, как на реальном устройстве."""
    queue = sorted(events, key=lambda e: e.at)
    idx = 0
    now = day
    end = day + timedelta(hours=hours)
    while now < end:
        while idx < len(queue) and queue[idx].at <= now:
            detector.feed(queue[idx])
            idx += 1
        detector.tick(now)
        now += TICK


def _train(rng: random.Random, days: int = 21) -> tuple[Baseline, datetime]:
    bl = Baseline()
    day = START
    for _ in range(days):
        bl.learn_day(normal_day(day, rng))
        day += timedelta(days=1)
    return bl, day


def evaluate(seed: int = 7, normal_days: int = 90, incident_runs: int = 30) -> dict:
    rng = random.Random(seed)
    baseline, day = _train(rng)

    # --- ложные тревоги на нормальных днях ---
    det = Detector(baseline=baseline)
    prompts_before = 0
    for _ in range(normal_days):
        events = with_heartbeats(normal_day(day, rng), day)
        # Человек отвечает на опрос устройства: нажимает кнопку через 1-4 мин.
        _run_with_human_response(det, events, day, rng)
        baseline.learn_day([e for e in events if e.is_activity])
        day += timedelta(days=1)
    false_alerts = len([a for a in det.alerts if a.severity >= Severity.ALERT])
    prompts = len(det.prompts) - prompts_before

    # --- обнаружение ЧП ---
    detected: dict[str, int] = {}
    latency_min: dict[str, list[float]] = {}
    scenarios = {
        "падение днём": scenario_fall_midday,
        "застрял в санузле": scenario_stuck_in_bathroom,
        "не встал утром": scenario_did_not_wake,
    }
    for name, gen in scenarios.items():
        hits, lat = 0, []
        for _ in range(incident_runs):
            d2 = Detector(baseline=baseline)
            events, incident = gen(day, rng)
            # В ЧП человек кнопку не нажимает — опрос остаётся без ответа.
            _run(d2, with_heartbeats(events, day), day)
            urgent = [a for a in d2.alerts if a.severity >= Severity.ALERT]
            if urgent:
                hits += 1
                lat.append((urgent[0].at - incident).total_seconds() / 60.0)
            day += timedelta(days=1)
        detected[name] = hits
        latency_min[name] = lat

    return {
        "normal_days": normal_days,
        "false_alerts": false_alerts,
        "false_alerts_per_month": false_alerts / normal_days * 30,
        "prompts_on_normal_days": prompts,
        "incident_runs": incident_runs,
        "detected": detected,
        "latency_min": latency_min,
    }


def _run_with_human_response(
    det: Detector, events: list[Event], day: datetime, rng: random.Random
) -> None:
    """Как _run, но человек жмёт кнопку в ответ на опрос — он же дома и в норме."""
    queue = sorted(events, key=lambda e: e.at)
    idx = 0
    now = day
    end = day + timedelta(hours=24)
    answered = 0
    while now < end:
        while idx < len(queue) and queue[idx].at <= now:
            det.feed(queue[idx])
            idx += 1
        det.tick(now)
        if det.pending is not None and answered <= len(det.prompts):
            delay = timedelta(minutes=rng.randint(1, 4))
            if now - det.pending.asked_at >= delay:
                det.feed(Event(now, EventKind.BUTTON))
                answered += 1
        now += TICK


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Измерение движка eldercare")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--days", type=int, default=90)
    args = ap.parse_args(argv)
    r = evaluate(seed=args.seed, normal_days=args.days)

    print(f"Нормальных дней: {r['normal_days']}")
    print(f"  Ложных тревог родне: {r['false_alerts']}"
          f"  ({r['false_alerts_per_month']:.2f} в месяц)")
    print(f"  Опросов самого человека: {r['prompts_on_normal_days']}"
          f"  ({r['prompts_on_normal_days'] / r['normal_days']:.2f} в день)")
    print(f"\nСценарии ЧП, прогонов каждого: {r['incident_runs']}")
    for name, hits in r["detected"].items():
        lat = r["latency_min"][name]
        avg = sum(lat) / len(lat) if lat else float("nan")
        print(f"  {name:22s} обнаружено {hits}/{r['incident_runs']}"
              f"  задержка в среднем {avg:.0f} мин")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
