"""Демо без железа: прогоняет сценарий и печатает то, что увидит оператор.

    python3 -m dronesentry.cli
"""
from __future__ import annotations

import argparse

from .fusion import Tracker
from .geo import Fix
from .protocol import decode, encode
from .targets import Detection, Source, TargetClass

OWN = Fix(50.4500, 30.5230, 120.0)

# Сценарий: кооперативный DJI висит в стороне, молчащий FPV идёт на носитель.
SCENARIO: list[tuple[float, Detection]] = [
    (0.0, Detection(0.0, Source.REMOTE_ID_WIFI, -58.0, 2437.0, ident="1581F5BHD24A0053",
                    target_fix=Fix(50.4530, 30.5300, 150.0))),
    (0.0, Detection(0.0, Source.VTX_SWEEP_58, -84.0, 5800.0, bearing_deg=215.0)),
    (2.0, Detection(2.0, Source.REMOTE_ID_WIFI, -58.0, 2437.0, ident="1581F5BHD24A0053",
                    target_fix=Fix(50.4530, 30.5300, 150.0))),
    (2.0, Detection(2.0, Source.VTX_SWEEP_58, -74.0, 5801.0, bearing_deg=212.0)),
    (4.0, Detection(4.0, Source.VTX_SWEEP_58, -66.0, 5800.0, bearing_deg=210.0)),
    (6.0, Detection(6.0, Source.VTX_SWEEP_58, -58.0, 5800.0, bearing_deg=208.0)),
]

_CLASS_RU = {
    TargetClass.COOPERATIVE: "кооперативный",
    TargetClass.EMITTING: "излучающий",
    TargetClass.SILENT: "молчащий",
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Демо-прогон DroneSentry без железа")
    ap.add_argument("--low-alt", action="store_true", help="модель затухания для малых высот")
    args = ap.parse_args(argv)

    tracker = Tracker(low_altitude=args.low_alt)
    tracker.set_own_fix(OWN)

    seq = 0
    last_t = -1.0
    for t, det in SCENARIO:
        tracker.update(det)
        if t == last_t:
            continue
        last_t = t
        tracker.prune(now_s=t)
        alerts = tracker.alerts()
        frame = encode(alerts, seq=seq, own_alt_m=OWN.alt)
        seq += 1
        print(f"\n--- t={t:.0f} с | кадр вниз {len(frame)} байт ---")
        _, _, reports = decode(frame)
        for a, rep in zip(alerts, reports):
            brg = "н/д" if rep.bearing_deg is None else f"{rep.bearing_deg:.0f}°"
            exact = "точно" if rep.range_exact else "оценка"
            print(
                f"[{a.level:8s}] #{rep.track_id} {_CLASS_RU[rep.target_class]:14s} "
                f"пеленг {brg:>5s}  {a.track.display_range():22s} ({exact})  {a.reason}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
