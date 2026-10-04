import math

import pytest

from dronesentry.fusion import TRACK_TIMEOUT_S, Tracker
from dronesentry.geo import Fix, bearing_deg, elevation_deg, slant_range_m
from dronesentry.protocol import decode, encode, frame_size, ident_hash
from dronesentry.rssi import bearing_from_two_antennas, estimate_range, fspl_db
from dronesentry.targets import Detection, Source, TargetClass

OWN = Fix(50.4500, 30.5230, 120.0)


def test_slant_range_uses_altitude_difference():
    target = Fix(50.4500, 30.5230, 220.0)
    assert slant_range_m(OWN, target) == pytest.approx(100.0, abs=0.5)


def test_bearing_north_and_east():
    assert bearing_deg(OWN, Fix(50.4600, 30.5230, 120)) == pytest.approx(0.0, abs=0.5)
    assert bearing_deg(OWN, Fix(50.4500, 30.5400, 120)) == pytest.approx(90.0, abs=0.5)


def test_elevation_sign():
    assert elevation_deg(OWN, Fix(50.4550, 30.5230, 320)) > 0
    assert elevation_deg(OWN, Fix(50.4550, 30.5230, 20)) < 0


def test_fspl_doubling_distance_costs_6db():
    assert fspl_db(2000, 5800) - fspl_db(1000, 5800) == pytest.approx(6.02, abs=0.05)


def test_rssi_estimate_is_an_interval_not_a_number():
    est = estimate_range(-70.0, 5800.0)
    assert est.min_m < est.best_m < est.max_m
    # Неизвестная мощность цели даёт разброс минимум в разы. Это признак
    # честной модели: если бы ratio был ~1, модель врала бы.
    assert est.uncertainty_ratio > 3.0


def test_stronger_signal_means_closer():
    near = estimate_range(-50.0, 5800.0)
    far = estimate_range(-85.0, 5800.0)
    assert near.best_m < far.best_m


def test_low_altitude_model_reports_shorter_range_for_same_rssi():
    assert estimate_range(-80.0, 5800.0, low_altitude=True).best_m < estimate_range(
        -80.0, 5800.0, low_altitude=False
    ).best_m


def test_two_antenna_bearing_refuses_when_target_outside_overlap():
    assert bearing_from_two_antennas(-40.0, -80.0, 0.0, 90.0) is None
    mid = bearing_from_two_antennas(-60.0, -60.0, 0.0, 90.0)
    assert mid == pytest.approx(45.0, abs=1.0)


def test_cooperative_track_gets_exact_range_relative_to_carrier():
    tr = Tracker()
    tr.set_own_fix(OWN)
    track = tr.update(
        Detection(
            t_s=0.0,
            source=Source.REMOTE_ID_WIFI,
            rssi_dbm=-60.0,
            freq_mhz=2437.0,
            ident="1596F3BDM24010ABCDEF",
            target_fix=Fix(50.4590, 30.5230, 170.0),
        )
    )
    assert track.target_class is TargetClass.COOPERATIVE
    assert track.range_is_exact
    assert track.range_m == pytest.approx(1002.0, abs=15.0)
    assert "м" in track.display_range() and "-" not in track.display_range()


def test_emitting_track_never_claims_exact_range():
    tr = Tracker()
    tr.set_own_fix(OWN)
    track = tr.update(
        Detection(t_s=0.0, source=Source.VTX_SWEEP_58, rssi_dbm=-72.0, freq_mhz=5800.0)
    )
    assert track.target_class is TargetClass.EMITTING
    assert not track.range_is_exact
    assert track.range_m is None
    assert track.range_estimate is not None


def test_detections_with_same_ident_merge_into_one_track():
    tr = Tracker()
    tr.set_own_fix(OWN)
    a = tr.update(
        Detection(0.0, Source.REMOTE_ID_WIFI, -60.0, 2437.0, ident="SN1",
                  target_fix=Fix(50.4590, 30.5230, 170.0))
    )
    b = tr.update(
        Detection(1.0, Source.REMOTE_ID_BLE, -62.0, 2402.0, ident="SN1",
                  target_fix=Fix(50.4580, 30.5230, 170.0))
    )
    assert a.track_id == b.track_id
    assert len(tr.tracks) == 1
    assert b.hits == 2


def test_nearby_vtx_channels_merge_but_distant_ones_do_not():
    tr = Tracker()
    tr.set_own_fix(OWN)
    first = tr.update(Detection(0.0, Source.VTX_SWEEP_58, -70.0, 5800.0))
    same = tr.update(Detection(0.5, Source.VTX_SWEEP_58, -71.0, 5805.0))
    other = tr.update(Detection(0.6, Source.VTX_SWEEP_58, -70.0, 5917.0))
    assert same.track_id == first.track_id
    assert other.track_id != first.track_id


def test_closing_speed_is_positive_when_target_approaches():
    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.DJI_DRONEID, -60.0, 2437.0, ident="SN2",
                        target_fix=Fix(50.4590, 30.5230, 120.0)))
    track = tr.update(Detection(2.0, Source.DJI_DRONEID, -58.0, 2437.0, ident="SN2",
                                target_fix=Fix(50.4580, 30.5230, 120.0)))
    assert track.closing_mps > 0


def test_fast_closing_distant_target_outranks_static_near_one():
    tr = Tracker()
    tr.set_own_fix(OWN)
    # Статичный на ~300 м
    tr.update(Detection(0.0, Source.DJI_DRONEID, -55.0, 2437.0, ident="STATIC",
                        target_fix=Fix(50.45270, 30.5230, 120.0)))
    tr.update(Detection(1.0, Source.DJI_DRONEID, -55.0, 2437.0, ident="STATIC",
                        target_fix=Fix(50.45270, 30.5230, 120.0)))
    # Идёт с 900 м на 800 м за 2 с => 50 м/с, время до контакта 16 с
    tr.update(Detection(0.0, Source.DJI_DRONEID, -70.0, 2437.0, ident="FAST",
                        target_fix=Fix(50.45810, 30.5230, 120.0)))
    tr.update(Detection(2.0, Source.DJI_DRONEID, -68.0, 2437.0, ident="FAST",
                        target_fix=Fix(50.45720, 30.5230, 120.0)))
    alerts = tr.alerts()
    assert alerts[0].track.ident == "FAST"
    assert alerts[0].level == "CRITICAL"


def test_prune_drops_stale_tracks_only():
    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.VTX_SWEEP_58, -70.0, 5800.0))
    tr.update(Detection(10.0, Source.VTX_SWEEP_58, -70.0, 5917.0))
    dead = tr.prune(now_s=10.0 + TRACK_TIMEOUT_S - 0.1)
    assert len(dead) == 1
    assert len(tr.tracks) == 1


def test_protocol_roundtrip_preserves_geometry():
    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.REMOTE_ID_WIFI, -60.0, 2437.0, ident="SN9",
                        target_fix=Fix(50.4590, 30.5230, 170.0)))
    tr.update(Detection(0.0, Source.VTX_SWEEP_58, -72.0, 5800.0, bearing_deg=270.0))
    alerts = tr.alerts()
    frame = encode(alerts, seq=7, own_alt_m=OWN.alt)
    assert len(frame) == frame_size(len(alerts))
    seq, own_alt, reports = decode(frame)
    assert seq == 7
    assert own_alt == pytest.approx(120.0)
    assert len(reports) == len(alerts)
    coop = next(r for r in reports if r.range_exact)
    assert coop.target_class is TargetClass.COOPERATIVE
    assert coop.range_m == pytest.approx(1002.0, abs=20.0)
    assert coop.ident_hash == ident_hash("SN9")
    emit = next(r for r in reports if not r.range_exact)
    assert emit.bearing_deg == pytest.approx(270.0, abs=1.5)


def test_decode_rejects_corrupted_frame():
    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.VTX_SWEEP_58, -70.0, 5800.0))
    frame = bytearray(encode(tr.alerts(), seq=1, own_alt_m=100.0))
    frame[4] ^= 0xFF
    with pytest.raises(ValueError, match="CRC"):
        decode(bytes(frame))


def test_frame_stays_within_lora_airtime_budget():
    tr = Tracker()
    tr.set_own_fix(OWN)
    for i in range(12):
        tr.update(Detection(0.0, Source.VTX_SWEEP_58, -70.0, 5650.0 + i * 20))
    frame = encode(tr.alerts(), seq=1, own_alt_m=100.0)
    # SF9/BW125 ~1.7 кбит/с; 1 Гц обновление => бюджет ~210 байт. Держимся много ниже.
    assert len(frame) <= 80
    _, _, reports = decode(frame)
    assert len(reports) == 8  # лишние цели отброшены, кадр остался валидным


def test_bearing_none_survives_roundtrip_as_unknown():
    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.VTX_SWEEP_58, -70.0, 5800.0))
    _, _, reports = decode(encode(tr.alerts(), seq=0, own_alt_m=0.0))
    assert reports[0].bearing_deg is None


def test_tracker_without_own_fix_still_reports_emitting_targets():
    """GPS модуля мог не захватить спутники — детекция обязана работать."""
    tr = Tracker()
    track = tr.update(Detection(0.0, Source.VTX_SWEEP_58, -70.0, 5800.0))
    assert track.range_estimate is not None
    assert math.isfinite(track.range_estimate.best_m)


def test_closing_speed_is_clamped_to_physically_possible():
    """RSSI-дистанция скачет, и без ограничения модуль рапортует 175 м/с."""
    from dronesentry.fusion import MAX_CLOSING_MPS

    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.VTX_SWEEP_58, -90.0, 5800.0))
    tr.update(Detection(0.5, Source.VTX_SWEEP_58, -45.0, 5800.0))
    track = next(iter(tr.tracks.values()))
    assert abs(track.closing_mps) <= MAX_CLOSING_MPS


def test_rssi_range_is_smoothed_not_taken_raw():
    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.VTX_SWEEP_58, -80.0, 5800.0))
    steady = next(iter(tr.tracks.values())).range_ema_m
    # Одиночный выброс в 30 дБ не должен утащить дистанцию к сырой оценке.
    tr.update(Detection(1.0, Source.VTX_SWEEP_58, -50.0, 5800.0))
    track = next(iter(tr.tracks.values()))
    raw_spike = track.range_estimate.best_m
    assert raw_spike < track.range_ema_m < steady


def test_estimated_kinematics_are_marked_as_approximate():
    tr = Tracker()
    tr.set_own_fix(OWN)
    tr.update(Detection(0.0, Source.VTX_SWEEP_58, -85.0, 5800.0))
    tr.update(Detection(2.0, Source.VTX_SWEEP_58, -70.0, 5800.0))
    emitting = tr.alerts()[0]
    assert "~" in emitting.reason

    tr2 = Tracker()
    tr2.set_own_fix(OWN)
    tr2.update(Detection(0.0, Source.DJI_DRONEID, -60.0, 2437.0, ident="SNX",
                         target_fix=Fix(50.4560, 30.5230, 120.0)))
    tr2.update(Detection(2.0, Source.DJI_DRONEID, -60.0, 2437.0, ident="SNX",
                         target_fix=Fix(50.4550, 30.5230, 120.0)))
    assert "~" not in tr2.alerts()[0].reason
