"""Тесты хост-инструмента этапа 1.

Прикрывают три дефекта, найденных независимыми проверками. Каждый из них
выглядел безобидно и каждый вёл к неверному решению о матрасе.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

import pytest

CAPTURE = Path(__file__).resolve().parent.parent / "утро" / "tools" / "capture.py"


def _load():
    """Инструмент — скрипт, а не пакет, поэтому грузим по пути.

    Регистрация в sys.modules обязательна: без неё dataclass внутри модуля
    падает, потому что не находит свой же модуль.
    """
    sys.path.insert(0, str(CAPTURE.parent.parent))
    spec = importlib.util.spec_from_file_location("utro_capture", CAPTURE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["utro_capture"] = mod
    spec.loader.exec_module(mod)
    return mod


cap = _load()


# --------------------------------------------------------------------------
# Режимы raw и mains были реализованы, но не зарегистрированы в argparse.
# Обязательная проверка наводки 50 Гц из-за этого не запускалась ни одним из
# способов, описанных в самом же инструменте.
# --------------------------------------------------------------------------

def test_all_five_modes_are_reachable():
    actions = cap.build_parser()._subparsers._group_actions[0].choices
    assert set(actions) == {"record", "replay", "live", "raw", "mains"}


def test_mandatory_mains_check_parses():
    """Команда, которую инструмент сам предписывает в ПОРЯДКЕ РАБОТЫ."""
    args = cap.build_parser().parse_args(["mains", "записи/raw4k.txt"])
    assert args.func is cap.cmd_mains
    assert args.file == "записи/raw4k.txt"


def test_raw_mode_parses_with_the_documented_arguments():
    args = cap.build_parser().parse_args(
        ["raw", "--port", "/dev/ttyACM0", "--out", "raw4k.txt", "--seconds", "10"]
    )
    assert args.func is cap.cmd_raw
    assert args.seconds == 10
    # cmd_raw читает оба этих поля; раньше их не определял ни один парсер.
    assert hasattr(args, "no_analyze") and hasattr(args, "note")


def test_raw_rejects_capture_longer_than_firmware_ram():
    """Прошивка держит в ОЗУ не больше 30 с."""
    with pytest.raises(SystemExit):
        cap.build_parser().parse_args(
            ["raw", "--port", "/dev/x", "--out", "o", "--seconds", "60"]
        )


def test_modes_without_analysis_args_do_not_crash_main():
    """main() безусловно читал args.step/args.window — у raw и mains их нет."""
    args = cap.build_parser().parse_args(["mains", "нет-такого-файла"])
    assert not hasattr(args, "step")
    with pytest.raises(SystemExit):
        cap.main(["mains", "нет-такого-файла"])


def test_warning_and_failure_have_different_exit_codes():
    """«На пределе» и «чинить механику» требуют разных действий."""
    assert cap.EXIT_MAINS_EDGE != cap.EXIT_MAINS_BAD
    codes = [
        cap.EXIT_PULSE_OK, cap.EXIT_NO_PULSE, cap.EXIT_NO_BREATHING,
        cap.EXIT_NO_VERDICT, cap.EXIT_DONE_NO_VERDICT, cap.EXIT_PULSE_SHAKY,
        cap.EXIT_MAINS_BAD, cap.EXIT_MAINS_EDGE,
    ]
    assert len(set(codes)) == len(codes)


def test_help_epilog_lists_the_mains_codes():
    text = cap.build_parser().format_help()
    assert "15" in text and "16" in text


# --------------------------------------------------------------------------
# Наводка 50 Гц считалась одним бином точно на 50.000 Гц по всей записи.
# Сеть номинал не держит, а на длинном окне амплитуда падает как sinc(dF*T):
# при уходе 0.1 Гц и окне 10 с оценка проваливается в нуль, то есть прибор
# рапортует «наводки нет» при любой реальной наводке.
# --------------------------------------------------------------------------

FS = 4000.0
SECONDS = 10.0
AMP = 150.0


def _mains_signal(freq: float, amp: float = AMP, seconds: float = SECONDS):
    n = int(FS * seconds)
    return [amp * math.sin(2 * math.pi * freq * i / FS) for i in range(n)]


def test_single_bin_estimate_collapses_under_realistic_drift():
    """Фиксируем сам дефект: наивный метод обязан провалиться."""
    sig = _mains_signal(50.1)
    naive = 2.0 * cap.goertzel(sig, FS, 50.0)
    assert naive < 0.05 * AMP, "если это перестало падать, тест потерял смысл"


@pytest.mark.parametrize("drift", [0.0, 0.02, 0.05, 0.1, 0.3, 0.5])
def test_mains_amplitude_survives_drift(drift):
    sig = _mains_signal(50.0 + drift)
    got = cap._mains_amp(sig, FS, 1)
    assert got == pytest.approx(AMP, rel=0.12), f"уход {drift} Гц"


def test_mains_harmonics_measured_with_scaled_probes():
    """k-я гармоника смещается на k*dF, опоры обязаны расходиться так же."""
    freq = 50.1
    n = int(FS * SECONDS)
    sig = [
        150 * math.sin(2 * math.pi * freq * i / FS)
        + 40 * math.sin(2 * math.pi * 2 * freq * i / FS)
        + 15 * math.sin(2 * math.pi * 3 * freq * i / FS)
        for i in range(n)
    ]
    assert cap._mains_amp(sig, FS, 1) == pytest.approx(150, rel=0.12)
    assert cap._mains_amp(sig, FS, 2) == pytest.approx(40, rel=0.15)
    assert cap._mains_amp(sig, FS, 3) == pytest.approx(15, rel=0.20)


def test_pure_noise_does_not_look_like_mains():
    rng = random.Random(1)
    noise = [rng.gauss(0.0, 20.0) for _ in range(int(FS * SECONDS))]
    assert cap._mains_amp(noise, FS, 1) < 5.0


def test_short_record_falls_back_instead_of_returning_zero():
    sig = _mains_signal(50.1, seconds=0.2)
    assert cap._mains_amp(sig, FS, 1) > 0.5 * AMP


# --------------------------------------------------------------------------
# Насыщение определялось «по плоской вершине», когда шины АЦП неизвестны.
# У мёртвого или недоусиленного тракта сигнал почти постоянный, экстремумы —
# самые частые значения, доля прижатых велика, и прибор объявлял насыщение с
# предписанием «уменьшите усиление» — противоположным верному.
# --------------------------------------------------------------------------

def _levels(values, rails=None):
    lo, hi = rails if rails else (None, None)
    acc = cap.LevelAccum(rail_lo=lo, rail_hi=hi)
    for v in values:
        acc.add(float(v))
    return acc.finish()


def test_dead_chain_is_not_declared_saturated():
    """Почти постоянный сигнал без шин: диагноза быть не должно."""
    st = _levels([1000] * 500 + [1030] * 500)
    assert not st.clipping
    assert st.clipping_unknown


def test_saturation_requires_known_rails():
    rails = (0.0, 4095.0 * 80.0)
    saturated = [rails[1]] * 60 + list(range(1000, 1940))
    st = _levels(saturated, rails=rails)
    assert st.clipping
    assert "шине АЦП" in st.clip_reason


def test_flat_top_without_rails_is_a_suspicion_not_a_diagnosis():
    st = _levels([5000] * 40 + list(range(5001, 5961)))
    assert not st.clipping
    assert st.flat_top_suspect


def test_level_report_says_saturation_was_not_checked():
    st = _levels([1000] * 500 + [1030] * 500)
    text = "\n".join(cap.levels_block(st))
    assert "ПРОВЕРИТЬ НЕЧЕМ" in text
    # Предписания по усилению в этой ветке быть не должно.
    assert "Уменьшите аналоговое усиление" not in text
