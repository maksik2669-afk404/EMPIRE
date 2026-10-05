import random
from datetime import datetime, timedelta

import pytest

from morning import synth
from morning.digest import render
from morning.dsp import (
    PEAK_SNR_RELIABLE,
    WindowResult,
    analyze_window,
    bandpass,
    goertzel,
    peaks,
)
from morning.night import RESP_MISSING_ALARM, NightRecorder
from morning.presence import BedFusion, BedState, LoadReading

FS = 200.0
DUR = 60.0
T0 = datetime(2026, 3, 10, 23, 0)


def _rng():
    return random.Random(4)


def _one_person(resp=15.0, hr=62.0, rng=None):
    rng = rng or _rng()
    return synth.mix(
        synth.breathing(DUR, FS, resp, 1.0),
        synth.heartbeats(DUR, FS, hr, 0.09),
        synth.noise(DUR, FS, 0.05, rng),
    )


# ---------- DSP ----------

def test_goertzel_finds_known_tone():
    sig = [__import__("math").sin(2 * 3.141592653589793 * 2.0 * i / FS) for i in range(2000)]
    assert goertzel(sig, FS, 2.0) > 20 * goertzel(sig, FS, 5.0)


def test_bandpass_rejects_out_of_band_tone():
    import math
    n = int(FS * 30)
    inband = [math.sin(2 * math.pi * 0.25 * i / FS) for i in range(n)]
    out = [math.sin(2 * math.pi * 50.0 * i / FS) for i in range(n)]
    f_in = bandpass(inband, 0.08, 0.7, FS)
    f_out = bandpass(out, 0.08, 0.7, FS)
    e_in = sum(x * x for x in f_in[int(FS * 5):])
    e_out = sum(x * x for x in f_out[int(FS * 5):])
    assert e_in > 100 * e_out


def test_peaks_respect_minimum_separation():
    bins = [(0.10, 1.0), (0.11, 0.9), (0.12, 0.8), (0.30, 0.7), (0.31, 0.6)]
    got = peaks(bins, 0.06)
    assert len(got) <= 2


def test_respiration_rate_recovered():
    for bpm in (10.0, 15.0, 20.0):
        r = analyze_window(_one_person(resp=bpm), FS)
        assert r.resp_bpm is not None
        assert r.resp_bpm == pytest.approx(bpm, abs=1.0)


def test_heart_rate_recovered_when_signal_is_strong():
    r = analyze_window(_one_person(resp=15.0, hr=62.0), FS)
    assert r.hr_bpm == pytest.approx(62.0, abs=3.0)


def _breathing_thumps(resp=15.0, amp=0.35, rng=None):
    """Дыхание с резким толчком вдоха и БЕЗ сердца вовсе.

    Толчок вдоха широкополосный, он попадает и в кардиополосу 4-20 Гц. Поезд
    таких толчков с частотой дыхания даёт в огибающей кардиополосы — ровно в
    той, по которой ищется пульс, — гребёнку на всех кратностях частоты
    дыхания. При 15 вд/мин это 30, 45, 60, 75, 90 в минуту, то есть вся полоса
    пульса. Поэтому synth.heartbeats здесь вызван с ЧАСТОТОЙ ДЫХАНИЯ: это не
    сердце, это форма дыхательного толчка.
    """
    rng = rng or _rng()
    return synth.mix(
        synth.breathing(DUR, FS, resp, 1.0),
        synth.heartbeats(DUR, FS, resp, amp),
        synth.noise(DUR, FS, 0.05, rng),
    )


def test_breathing_harmonic_is_not_reported_as_pulse():
    """Сердца в сигнале нет вовсе, а гармоника дыхания стоит в полосе пульса и
    выглядит уверенным пиком. Ошибка такого рода неотличима от успеха, поэтому
    проверяем и то, что пик действительно уверенный."""
    r = analyze_window(_breathing_thumps(resp=15.0, amp=0.35), FS)
    assert r.resp_bpm == pytest.approx(15.0, abs=1.0)
    # Без проверки на гармонику это число было бы выдано человеку как пульс.
    assert r.hr_snr >= PEAK_SNR_RELIABLE
    assert r.hr_bpm is None
    assert r.hr_harmonic_suspect
    assert r.hr_resp_harmonic is not None


def test_breathing_harmonic_refused_at_several_rates():
    """Отказ не должен зависеть от того, на какую кратность попала гребёнка."""
    for resp in (12.0, 15.0, 18.0, 22.0):
        r = analyze_window(_breathing_thumps(resp=resp, amp=0.6), FS)
        assert r.hr_bpm is None, f"выдан пульс {r.hr_bpm} при дыхании {resp} без сердца"
        assert r.hr_harmonic_suspect


def test_real_pulse_exactly_on_resp_multiple_is_kept():
    """Пульс 60 при дыхании 15 — ровно 4-я кратность. Выбрасывать его нельзя:
    такое совпадение случается само собой, а не только у гармоники. Различает
    не близость частот, а то, насколько пик выше остальной гребёнки."""
    r = analyze_window(_one_person(resp=15.0, hr=60.0), FS)
    assert r.hr_resp_harmonic == 4            # близость к кратности замечена
    assert not r.hr_harmonic_suspect          # но пик выделяется над гребёнкой
    assert r.hr_comb_dominance is not None and r.hr_comb_dominance > 2.0
    assert r.hr_bpm == pytest.approx(60.0, abs=3.0)


def test_real_pulse_near_multiple_kept_across_rates():
    for resp, hr in ((15.0, 60.0), (20.0, 60.0), (15.0, 75.0), (12.0, 72.0), (18.0, 72.0)):
        r = analyze_window(_one_person(resp=resp, hr=hr), FS)
        assert r.hr_bpm == pytest.approx(hr, abs=3.0), (
            f"потерян настоящий пульс {hr} при дыхании {resp}"
        )


def test_harmonic_check_is_silent_when_pulse_is_far_from_multiple():
    """85 уд/мин при дыхании 15 — это 5.67 кратности, ни на что не похоже.
    Признаки гармоники не должны выставляться на пустом месте."""
    r = analyze_window(_one_person(resp=15.0, hr=85.0), FS)
    assert r.hr_bpm == pytest.approx(85.0, abs=3.0)
    assert r.hr_resp_harmonic is None
    assert not r.hr_harmonic_suspect
    assert r.hr_comb_dominance is None


def test_window_result_still_builds_from_seven_positional_fields():
    """night.py, hub/system.py и часть тестов создают WindowResult позиционно
    из семи полей. Новые поля обязаны иметь значения по умолчанию."""
    w = WindowResult(True, 1, 15.0, 62.0, False, 40.0, 9.0)
    assert not w.hr_harmonic_suspect
    assert w.hr_resp_harmonic is None
    assert w.hr_comb_dominance is None
    assert w.resp_reliable


def test_empty_bed_is_not_reported_occupied():
    r = analyze_window(synth.empty_bed(DUR, FS, 0.05, _rng()), FS)
    assert not r.occupied
    assert r.occupants == 0
    assert r.resp_bpm is None and r.hr_bpm is None


def test_two_people_detected_and_pulse_refused():
    """Выдать один пульс на двоих — значит соврать. Отказ обязателен."""
    rng = _rng()
    sig = synth.mix(
        synth.breathing(DUR, FS, 15.0, 1.0),
        synth.breathing(DUR, FS, 19.0, 0.9, phase=1.1),
        synth.heartbeats(DUR, FS, 62.0, 0.09),
        synth.heartbeats(DUR, FS, 71.0, 0.08),
        synth.noise(DUR, FS, 0.05, rng),
    )
    r = analyze_window(sig, FS)
    assert r.occupants == 2
    assert r.hr_bpm is None


def test_motion_marks_window_unreliable():
    rng = _rng()
    sig = synth.motion_burst(_one_person(rng=rng), FS, 30.0, 3.0, 1.5, rng)
    r = analyze_window(sig, FS)
    assert r.motion
    assert r.hr_bpm is None
    assert not r.resp_reliable


def test_short_window_returns_nothing_instead_of_guessing():
    r = analyze_window(_one_person()[: int(FS * 5)], FS)
    assert not r.occupied and r.resp_bpm is None


# ---------- слияние датчиков ----------

def test_load_cells_distinguish_one_from_two():
    f = BedFusion()
    f.feed_load(LoadReading(T0, left_kg=62.0, right_kg=1.0))
    assert f.state is BedState.ONE
    f.feed_load(LoadReading(T0, left_kg=62.0, right_kg=71.0))
    assert f.state is BedState.TWO
    f.feed_load(LoadReading(T0, left_kg=0.5, right_kg=0.4))
    assert f.state is BedState.EMPTY


def test_blanket_is_not_mistaken_for_a_second_person():
    f = BedFusion()
    f.feed_load(LoadReading(T0, left_kg=64.0, right_kg=6.0))
    assert f.state is BedState.ONE


def test_weight_reported_only_for_a_single_occupant():
    f = BedFusion()
    for _ in range(5):
        f.feed_load(LoadReading(T0, left_kg=60.0, right_kg=2.0))
    assert f.weight_kg == pytest.approx(62.0, abs=0.5)
    f.feed_load(LoadReading(T0, left_kg=60.0, right_kg=70.0))
    assert f.weight_kg is None


def test_night_alarm_impossible_without_load_channel():
    """Главное требование: одна плёнка не имеет права будить родню.

    Без статического канала «дыхания нет» означает в том числе «встал».
    """
    f = BedFusion()
    f.feed_window(T0, WindowResult(True, 1, 15.0, 62.0, False, 40.0, 9.0))
    later = T0 + timedelta(minutes=10)
    assert not f.can_raise_night_alarm(later, RESP_MISSING_ALARM)


def test_night_alarm_blocked_when_person_left_the_bed():
    f = BedFusion()
    f.feed_load(LoadReading(T0, left_kg=62.0, right_kg=1.0))
    f.feed_window(T0, WindowResult(True, 1, 15.0, 62.0, False, 40.0, 9.0))
    # Встал: нагрузка ушла.
    t = T0 + timedelta(minutes=10)
    f.feed_load(LoadReading(t, left_kg=0.3, right_kg=0.2))
    assert not f.can_raise_night_alarm(t, RESP_MISSING_ALARM)


def test_night_alarm_blocked_by_room_motion():
    f = BedFusion()
    f.feed_load(LoadReading(T0, left_kg=62.0, right_kg=1.0))
    f.feed_window(T0, WindowResult(True, 1, 15.0, 62.0, False, 40.0, 9.0))
    t = T0 + timedelta(minutes=10)
    f.feed_load(LoadReading(t, left_kg=62.0, right_kg=1.0))
    f.feed_room_motion(t - timedelta(minutes=1))
    assert not f.can_raise_night_alarm(t, RESP_MISSING_ALARM)


def test_night_alarm_raised_when_all_three_conditions_hold():
    f = BedFusion()
    f.feed_load(LoadReading(T0, left_kg=62.0, right_kg=1.0))
    f.feed_window(T0, WindowResult(True, 1, 15.0, 62.0, False, 40.0, 9.0))
    t = T0 + timedelta(minutes=10)
    f.feed_load(LoadReading(t, left_kg=62.0, right_kg=1.0))
    assert f.can_raise_night_alarm(t, RESP_MISSING_ALARM)


# ---------- ночь и сводка ----------

def _good(resp=15.0, hr=62.0):
    return WindowResult(True, 1, resp, hr, False, 40.0, 9.0)


def _no_resp():
    return WindowResult(True, 1, None, None, False, 1.0, 0.0)


def test_night_aggregates_hr_only_from_consistent_blocks():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for i in range(60):
        f.feed_load(LoadReading(t, 62.0, 1.0))
        # Разброс внутри блока мал — блоки принимаются.
        rec.feed(t, _good(hr=61.0 + (i % 3)))
        t += timedelta(minutes=1)
    s = rec.finish(t)
    assert s.hr_bpm_median == pytest.approx(62.0, abs=2.0)
    assert s.resp_bpm_median == pytest.approx(15.0, abs=0.5)
    assert s.time_in_bed == timedelta(minutes=60)


def test_wild_hr_scatter_is_discarded_not_averaged():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for i in range(45):
        f.feed_load(LoadReading(t, 62.0, 1.0))
        rec.feed(t, _good(hr=50.0 + (i % 2) * 40.0))   # прыжки 50/90
        t += timedelta(minutes=1)
    assert rec.finish(t).hr_bpm_median is None


def test_awakening_counted_when_bed_is_empty_long_enough():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for _ in range(20):
        f.feed_load(LoadReading(t, 62.0, 1.0)); rec.feed(t, _good()); t += timedelta(minutes=1)
    for _ in range(8):
        f.feed_load(LoadReading(t, 0.2, 0.1)); rec.feed(t, _no_resp()); t += timedelta(minutes=1)
    for _ in range(20):
        f.feed_load(LoadReading(t, 62.0, 1.0)); rec.feed(t, _good()); t += timedelta(minutes=1)
    s = rec.finish(t)
    assert s.awakenings == 1


def test_resp_gap_while_out_of_bed_is_not_an_alarm():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for _ in range(10):
        f.feed_load(LoadReading(t, 62.0, 1.0)); rec.feed(t, _good()); t += timedelta(minutes=1)
    for _ in range(12):
        f.feed_load(LoadReading(t, 0.2, 0.1)); rec.feed(t, _no_resp()); t += timedelta(minutes=1)
    s = rec.finish(t)
    assert s.alarms == []
    assert "не регистрировалось" not in render(s)


def test_resp_gap_in_bed_without_motion_becomes_an_alarm():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for _ in range(10):
        f.feed_load(LoadReading(t, 62.0, 1.0)); rec.feed(t, _good()); t += timedelta(minutes=1)
    for _ in range(8):
        f.feed_load(LoadReading(t, 62.0, 1.0)); rec.feed(t, _no_resp()); t += timedelta(minutes=1)
    s = rec.finish(t)
    assert len(s.alarms) == 1
    text = render(s)
    assert "не регистрировалось" in text
    # Формулировка — состояние датчика, не диагноз. Этого слова быть не должно.
    assert "остановка дыхания" not in text.lower()
    assert "апноэ" not in text.lower()


def test_digest_reads_like_a_message_not_a_report():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for _ in range(45):
        f.feed_load(LoadReading(t, 60.0, 2.0)); rec.feed(t, _good(hr=62.0)); t += timedelta(minutes=1)
    s = rec.finish(t)
    text = render(s, name="мама", weight_baseline_kg=62.0)
    assert text.startswith("Доброе утро")
    assert "Ночью не вставала" in text
    assert "как обычно" in text


def test_digest_flags_weight_gain_without_diagnosing():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for _ in range(45):
        f.feed_load(LoadReading(t, 63.0, 2.0)); rec.feed(t, _good()); t += timedelta(minutes=1)
    s = rec.finish(t)
    text = render(s, weight_baseline_kg=62.0)
    assert "скажите врачу" in text
    assert "сердечн" not in text.lower()   # диагноз не ставим


def test_digest_handles_empty_bed_night():
    f = BedFusion()
    rec = NightRecorder(f)
    rec.start_night(T0)
    t = T0
    for _ in range(30):
        f.feed_load(LoadReading(t, 0.1, 0.1)); rec.feed(t, _no_resp()); t += timedelta(minutes=1)
    assert "в постели" in render(rec.finish(t), name="мама").lower()
