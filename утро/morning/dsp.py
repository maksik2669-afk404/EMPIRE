"""Обработка сигнала пьезоплёнки PVDF под матрасом.

Баллистокардиография: плёнка регистрирует механические толчки тела. Дыхание —
медленная крупная составляющая, сердце — быстрые слабые толчки поверх.

Чистый Python без numpy намеренно: ровно этот же алгоритм должен переноситься
на ESP32 в фиксированной точке. Все фильтры — биквады, вся спектральная
оценка — Гёрцель по сетке частот, никаких FFT-библиотек.

Важное физическое ограничение PVDF: плёнка отдаёт ЗАРЯД, то есть реагирует на
изменение деформации, а не на её величину. Статический вес человека она не
видит. Поэтому «человек в постели» определяется по наличию дыхания, и отсюда
следует, что пропажа дыхания неотличима от ухода с кровати — без подтверждения
от стационарных датчиков ночную тревогу давать нельзя.

Второе ограничение, такое же принципиальное: дыхание и пульс здесь не
независимы. Кратности частоты дыхания попадают ровно в полосу пульса (15 вд/мин
даёт 30, 45, 60, 75, 90 уд/мин), а дыхательный толчок широкополосный и доходит
до кардиополосы. Поэтому сильная гармоника дыхания выглядит уверенным пульсом,
и это самая опасная ошибка модуля: она неотличима от успеха. Разбор — в
_resp_harmonic_check, отказ виден в поле hr_harmonic_suspect.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Полоса дыхания: 0.08-0.7 Гц это 4.8-42 вдоха в минуту. Нижняя граница
# захватывает очень медленное дыхание во сне, верхняя — тахипноэ.
RESP_LO_HZ = 0.08
RESP_HI_HZ = 0.70
# Полоса сердечных толчков в BCG. Ниже 4 Гц мешает дыхание, выше 20 Гц
# начинается шум плёнки и наводки.
CARD_LO_HZ = 4.0
CARD_HI_HZ = 20.0
# Полоса частоты пульса: 40-130 уд/мин.
HR_LO_HZ = 0.67
HR_HI_HZ = 2.17

# Рабочие частоты после децимации.
FS_RESP = 10.0
FS_CARD = 50.0

# Порог уверенности: во сколько раз пик спектра должен превышать медиану.
# Подбирается на синтетике и перепроверяется на реальных записях.
PEAK_SNR_OCCUPIED = 4.0
PEAK_SNR_RELIABLE = 6.0
# Второй человек: второй пик не ниже этой доли главного и отстоит не меньше,
# чем на RESP_MIN_SEPARATION_HZ.
SECOND_PERSON_RATIO = 0.55
RESP_MIN_SEPARATION_HZ = 0.06
# Шевеление: всплеск энергии в кардиополосе относительно медианы окна.
MOTION_RATIO = 6.0

# --- защита от гармоник дыхания в полосе пульса ---
# Дыхание 15 вд/мин даёт гребёнку на 30, 45, 60, 75 ... в минуту, то есть ровно
# в полосе пульса. Толчок вдоха широкополосный, он попадает и в кардиополосу
# 4-20 Гц, а значит огибающая кардиополосы — та самая, по которой мы ищем
# пульс, — содержит всю эту гребёнку. Проверено на синтетике: вдохи без всякого
# сердца дают «пульс» 54, 60, 66, 84 уд/мин с уверенностью 7-19, то есть выше
# PEAK_SNR_RELIABLE. Ошибка неотличима от успеха, и человеку её не видно.
#
# Допуск на попадание в кратность: он ОБЯЗАН расти с номером кратности k.
# Частота дыхания известна с точностью порядка шага сетки спектра дыхания
# (0.005 Гц), и ошибка предсказания k-й гармоники равна k * этой ошибки.
# Плюс собственное размытие линии в окне 60 с: 1/60 = 0.017 Гц.
# Отсюда HARMONIC_TOL_BASE_HZ + k * HARMONIC_TOL_PER_K_HZ.
HARMONIC_TOL_BASE_HZ = 0.015
HARMONIC_TOL_PER_K_HZ = 0.005
# Ограничение сверху: зона подозрения не должна сомкнуться с соседней
# кратностью, иначе при медленном дыхании (6 вд/мин, кратности через 0.1 Гц)
# подозрительной становится вся полоса и правило перестаёт что-либо значить.
# 0.35 оставляет между зонами просвет в 30 % расстояния между кратностями.
HARMONIC_TOL_MAX_FRACTION = 0.35
# Во сколько раз кандидат должен превысить МЕДИАНУ остальных членов гребёнки,
# чтобы считаться настоящим пульсом, случайно оказавшимся у кратности.
# Измерено на синтетике (сетка 3 шума x 6 частот дыхания x 7 частот пульса):
# у настоящего пульса рядом с кратностью превышение 2.8-7.5, у гармоники
# дыхания 1.05-1.5. Порог 2.0 стоит примерно посередине в логарифмической
# шкале. НА ЖЕЛЕЗЕ НЕ ПРОВЕРЕН: на реальном матрасе дыхательная гребёнка может
# быть неравномерной (резонансы матраса подчёркивают отдельные её члены), и
# тогда превышение у гармоники окажется выше. Порог придётся перемерить по
# записям теста Б из АНАЛОГОВЫЙ-ТРАКТ.md §6.5 — до тех пор он ориентировочный.
HARMONIC_COMB_DOMINANCE = 2.0
# Шаг перебора при поиске члена гребёнки около предсказанной частоты.
# Вдвое мельче сетки спектра пульса (0.01 Гц): член гребёнки ищется точнее,
# чем кандидат, иначе сравнение занижает гребёнку и оправдывает гармонику.
HARMONIC_PROBE_STEP_HZ = 0.005


class Biquad:
    """Биквад прямой формы 1. Коэффициенты по рецептам RBJ."""

    __slots__ = ("b0", "b1", "b2", "a1", "a2", "_x1", "_x2", "_y1", "_y2")

    def __init__(self, b0: float, b1: float, b2: float, a0: float, a1: float, a2: float):
        self.b0, self.b1, self.b2 = b0 / a0, b1 / a0, b2 / a0
        self.a1, self.a2 = a1 / a0, a2 / a0
        self._x1 = self._x2 = self._y1 = self._y2 = 0.0

    def reset(self) -> None:
        self._x1 = self._x2 = self._y1 = self._y2 = 0.0

    def step(self, x: float) -> float:
        y = (
            self.b0 * x + self.b1 * self._x1 + self.b2 * self._x2
            - self.a1 * self._y1 - self.a2 * self._y2
        )
        self._x2, self._x1 = self._x1, x
        self._y2, self._y1 = self._y1, y
        return y

    def run(self, xs: list[float]) -> list[float]:
        return [self.step(x) for x in xs]


def lowpass(fc: float, fs: float, q: float = 0.7071) -> Biquad:
    w0 = 2.0 * math.pi * fc / fs
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    return Biquad((1 - cw) / 2, 1 - cw, (1 - cw) / 2, 1 + alpha, -2 * cw, 1 - alpha)


def highpass(fc: float, fs: float, q: float = 0.7071) -> Biquad:
    w0 = 2.0 * math.pi * fc / fs
    cw, sw = math.cos(w0), math.sin(w0)
    alpha = sw / (2.0 * q)
    return Biquad((1 + cw) / 2, -(1 + cw), (1 + cw) / 2, 1 + alpha, -2 * cw, 1 - alpha)


def bandpass(xs: list[float], lo: float, hi: float, fs: float) -> list[float]:
    """Каскад ФВЧ+ФНЧ. Прогоняется дважды, вперёд и назад, чтобы убрать
    фазовый сдвиг — для оценки частоты это важнее крутизны."""
    out = lowpass(hi, fs).run(highpass(lo, fs).run(xs))
    out = lowpass(hi, fs).run(highpass(lo, fs).run(out[::-1]))[::-1]
    return out


def decimate(xs: list[float], fs: float, fs_target: float) -> tuple[list[float], float]:
    """Антиалиасинговый ФНЧ и прореживание. Возвращает сигнал и новую частоту."""
    factor = max(1, int(round(fs / fs_target)))
    if factor == 1:
        return list(xs), fs
    filt = lowpass(fs_target / 2.5, fs).run(xs)
    return filt[::factor], fs / factor


def goertzel(xs: list[float], fs: float, freq: float) -> float:
    """Амплитуда одной частоты. Дешевле полного спектра и достаточно."""
    n = len(xs)
    if n == 0:
        return 0.0
    w = 2.0 * math.pi * freq / fs
    coeff = 2.0 * math.cos(w)
    s1 = s2 = 0.0
    for x in xs:
        s0 = x + coeff * s1 - s2
        s2, s1 = s1, s0
    power = s1 * s1 + s2 * s2 - coeff * s1 * s2
    return math.sqrt(max(0.0, power)) / n


def spectrum(xs: list[float], fs: float, lo: float, hi: float, step: float) -> list[tuple[float, float]]:
    bins: list[tuple[float, float]] = []
    f = lo
    while f <= hi + 1e-9:
        bins.append((f, goertzel(xs, fs, f)))
        f += step
    return bins


def _median(vals: list[float]) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2.0


def _rms(xs: list[float]) -> float:
    return math.sqrt(sum(x * x for x in xs) / len(xs)) if xs else 0.0


def peaks(bins: list[tuple[float, float]], min_separation_hz: float) -> list[tuple[float, float]]:
    """Локальные максимумы, отсортированные по убыванию амплитуды,
    разнесённые не ближе min_separation_hz."""
    local = [
        bins[i]
        for i in range(1, len(bins) - 1)
        if bins[i][1] >= bins[i - 1][1] and bins[i][1] > bins[i + 1][1]
    ]
    local.sort(key=lambda p: -p[1])
    out: list[tuple[float, float]] = []
    for f, a in local:
        if all(abs(f - g) >= min_separation_hz for g, _ in out):
            out.append((f, a))
    return out


@dataclass
class WindowResult:
    """Итог одного окна анализа, обычно 60 секунд."""

    occupied: bool
    occupants: int              # 0, 1 или 2 — больше не различаем
    resp_bpm: float | None      # вдохов в минуту
    hr_bpm: float | None        # ударов в минуту
    motion: bool                # шевеление: витальные показатели недостоверны
    resp_snr: float
    hr_snr: float
    # Ниже — поля, добавленные после поля hr_snr и только со значениями по
    # умолчанию: WindowResult создаётся позиционно в night.py, hub/system.py и
    # в тестах, и порядок первых семи полей менять нельзя.
    hr_harmonic_suspect: bool = False   # пик пульса отвергнут: похож на гармонику дыхания
    hr_resp_harmonic: int | None = None # номер кратности k, если пик у кратности
    hr_comb_dominance: float | None = None  # во сколько раз пик выше остальной гребёнки

    @property
    def resp_reliable(self) -> bool:
        return self.resp_bpm is not None and not self.motion


def analyze_window(samples: list[float], fs: float = 200.0) -> WindowResult:
    """Разобрать окно сигнала плёнки.

    Отказ от выдачи числа — штатный результат. Пульс не выдаётся вовсе при двух
    людях в постели, при шевелении и когда найденный пик похож на гармонику
    дыхания (hr_harmonic_suspect): лучше None, чем правдоподобное врание.
    """
    if len(samples) < int(fs * 20):
        return WindowResult(False, 0, None, None, False, 0.0, 0.0)

    # --- шевеление: всплески в кардиополосе ---
    card_fs_sig, card_fs = decimate(samples, fs, FS_CARD)
    card = bandpass(card_fs_sig, CARD_LO_HZ, min(CARD_HI_HZ, card_fs / 2.5), card_fs)
    chunk = max(1, int(card_fs))          # по секунде
    rms_per_sec = [
        _rms(card[i : i + chunk]) for i in range(0, len(card) - chunk + 1, chunk)
    ]
    med_rms = _median(rms_per_sec)
    motion = bool(med_rms > 0 and max(rms_per_sec, default=0.0) > MOTION_RATIO * med_rms)

    # --- дыхание ---
    resp_sig, resp_fs = decimate(samples, fs, FS_RESP)
    resp = bandpass(resp_sig, RESP_LO_HZ, RESP_HI_HZ, resp_fs)
    resp_bins = spectrum(resp, resp_fs, RESP_LO_HZ, RESP_HI_HZ, 0.005)
    resp_floor = _median([a for _, a in resp_bins]) or 1e-12
    resp_peaks = peaks(resp_bins, RESP_MIN_SEPARATION_HZ)
    resp_snr = resp_peaks[0][1] / resp_floor if resp_peaks else 0.0

    occupants = 0
    resp_bpm: float | None = None
    if resp_snr >= PEAK_SNR_OCCUPIED:
        occupants = 1
        resp_bpm = resp_peaks[0][0] * 60.0
        if (
            len(resp_peaks) > 1
            and resp_peaks[1][1] >= SECOND_PERSON_RATIO * resp_peaks[0][1]
            and resp_peaks[1][1] / resp_floor >= PEAK_SNR_OCCUPIED
        ):
            occupants = 2

    occupied = occupants > 0 or motion

    # --- пульс: только один человек, без шевеления ---
    hr_bpm: float | None = None
    hr_snr = 0.0
    hr_harmonic_suspect = False
    hr_resp_harmonic: int | None = None
    hr_comb_dominance: float | None = None
    if occupants == 1 and not motion:
        env, env_fs = _envelope(card, card_fs)
        hr_bins = spectrum(env, env_fs, HR_LO_HZ, HR_HI_HZ, 0.01)
        hr_floor = _median([a for _, a in hr_bins]) or 1e-12
        hr_peaks = peaks(hr_bins, 0.05)
        if hr_peaks:
            hr_f, hr_amp = hr_peaks[0]
            hr_snr = hr_amp / hr_floor
            if hr_snr >= PEAK_SNR_RELIABLE:
                hr_harmonic_suspect, hr_resp_harmonic, hr_comb_dominance = (
                    _resp_harmonic_check(env, env_fs, hr_f, resp_bpm, hr_amp)
                )
                if not hr_harmonic_suspect:
                    hr_bpm = hr_f * 60.0
                # Второй пик как замена отвергнутому первому НЕ берётся: у
                # дыхательной гребёнки второй пик — такая же её кратность, и
                # подстановка выдала бы ту же ошибку другим числом.

    return WindowResult(
        occupied=occupied,
        occupants=occupants,
        resp_bpm=resp_bpm,
        hr_bpm=hr_bpm,
        motion=motion,
        resp_snr=resp_snr,
        hr_snr=hr_snr,
        hr_harmonic_suspect=hr_harmonic_suspect,
        hr_resp_harmonic=hr_resp_harmonic,
        hr_comb_dominance=hr_comb_dominance,
    )


def _harmonic_tolerance_hz(k: int, f_resp: float) -> float:
    """Полуширина зоны подозрения вокруг k-й кратности частоты дыхания."""
    tol = HARMONIC_TOL_BASE_HZ + k * HARMONIC_TOL_PER_K_HZ
    return min(tol, HARMONIC_TOL_MAX_FRACTION * f_resp)


def _comb_member_amplitude(env: list[float], env_fs: float, f: float, tol: float) -> float:
    """Амплитуда гребёнки около частоты f: максимум по узкой сетке ±tol.

    Перебор, а не одно значение в точке f: предсказание m*f_resp смещено ровно
    на те же tol, что и кандидат. Если кандидата брать по максимуму пика, а
    члены гребёнки — точно в предсказанной точке, то гребёнка окажется занижена
    и любая гармоника будет оправдана."""
    steps = max(1, int(round(tol / HARMONIC_PROBE_STEP_HZ)))
    return max(
        goertzel(env, env_fs, f + d * HARMONIC_PROBE_STEP_HZ)
        for d in range(-steps, steps + 1)
        if f + d * HARMONIC_PROBE_STEP_HZ > 0.0
    )


def _resp_harmonic_check(
    env: list[float],
    env_fs: float,
    hr_f: float,
    resp_bpm: float | None,
    hr_amp: float,
) -> tuple[bool, int | None, float | None]:
    """Не является ли найденный пик пульса гармоникой дыхания.

    Возвращает (подозрителен, номер кратности, превышение над гребёнкой).

    ПОЧЕМУ НЕ ПРОСТО ПО БЛИЗОСТИ ЧАСТОТ. Допуск обязан расти с номером
    кратности (см. HARMONIC_TOL_PER_K_HZ), и на k=8 зона подозрения — уже
    ±0.055 Гц, то есть ±3.3 уд/мин. Отказывать во всей этой зоне значит
    выбрасывать настоящий пульс постоянно: на сетке синтетики настоящий пульс
    попадал в зону подозрения примерно в трети случаев. Близость частот сама по
    себе ничего не решает.

    ЧТО РАЗЛИЧАЕТ ЛУЧШЕ. Дыхание входит в огибающую кардиополосы не одной
    линией, а полной гребёнкой: толчок вдоха короткий, поэтому в огибающей
    сидят ВСЕ кратности f_resp примерно одной силы. Сердце даёт одну линию
    (плюс свою вторую гармонику). Значит сравнивать надо кандидата с ОСТАЛЬНЫМИ
    членами гребёнки: если он лишь немногим выше них — он её член; если он
    выделяется в разы — это сердце, случайно оказавшееся у кратности.
    Берём МЕДИАНУ остальных членов, а не максимум: один член может быть поднят
    шумом или собственной второй гармоникой пульса, и максимум тогда оправдает
    гармонику дыхания, а медиана устойчива.

    ЧЕГО ЗДЕСЬ СДЕЛАТЬ НЕЛЬЗЯ. Самый надёжный признак — держится ли отношение
    пульса к дыханию постоянным, когда дыхание меняется: у гармоники отношение
    остаётся целым, у сердца уезжает. Это сравнение МЕЖДУ окнами, а одно окно
    его не содержит; место ему в night.py или на хосте, здесь его нет честно.
    Поэтому в пределах окна решение консервативное: если различить не удаётся,
    числа не выдаём.
    """
    if not resp_bpm or resp_bpm <= 0.0:
        # Пульс считается только при occupants == 1, а там дыхание найдено.
        # Если всё же нет — сравнивать не с чем, отказываем.
        return True, None, None

    f_resp = resp_bpm / 60.0
    k = int(round(hr_f / f_resp))
    if k < 1:
        return False, None, None
    tol = _harmonic_tolerance_hz(k, f_resp)
    if abs(hr_f - k * f_resp) > tol:
        return False, None, None

    # Выше этой частоты огибающая уже придавлена своим ФНЧ (см. _envelope),
    # и амплитуды членов гребёнки там занижены — сравнивать нельзя.
    env_hi = min(HR_HI_HZ * 1.5, env_fs / 2.5)
    others: list[float] = []
    m = 1
    while m * f_resp <= env_hi:
        if m != k:
            others.append(
                _comb_member_amplitude(
                    env, env_fs, m * f_resp, _harmonic_tolerance_hz(m, f_resp)
                )
            )
        m += 1

    comb = _median(others)
    if not others or comb <= 0.0:
        # Сравнивать не с чем: гребёнка не измерима. Отказываем — молчание
        # дешевле гармоники, выданной за пульс.
        return True, k, None
    dominance = hr_amp / comb
    return dominance < HARMONIC_COMB_DOMINANCE, k, dominance


def _envelope(card: list[float], fs: float) -> tuple[list[float], float]:
    """Огибающая кардиополосы: выпрямление и ФНЧ. Частота толчков сердца
    становится частотой огибающей."""
    rect = [abs(x) for x in card]
    smoothed = lowpass(HR_HI_HZ * 1.5, fs).run(rect)
    env, env_fs = decimate(smoothed, fs, FS_RESP)
    mean = sum(env) / len(env) if env else 0.0
    return [x - mean for x in env], env_fs
