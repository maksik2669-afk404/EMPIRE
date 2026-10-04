"""Синтез сигнала плёнки для тестов и калибровки порогов.

Сердечная составляющая моделируется затухающими всплесками, а не синусом:
в баллистокардиограмме сердце даёт серию толчков, и алгоритм обязан находить
их частоту по огибающей, а не по основному тону.
"""
from __future__ import annotations

import math
import random


def breathing(
    duration_s: float,
    fs: float,
    bpm: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
) -> list[float]:
    f = bpm / 60.0
    n = int(duration_s * fs)
    # Вдох короче выдоха — добавляем вторую гармонику, как в реальном дыхании.
    return [
        amplitude
        * (
            math.sin(2 * math.pi * f * i / fs + phase)
            + 0.25 * math.sin(4 * math.pi * f * i / fs + phase)
        )
        for i in range(n)
    ]


def heartbeats(
    duration_s: float,
    fs: float,
    bpm: float,
    amplitude: float = 0.08,
    ring_hz: float = 9.0,
    decay_s: float = 0.06,
) -> list[float]:
    """Поезд затухающих толчков с частотой пульса."""
    n = int(duration_s * fs)
    out = [0.0] * n
    period = 60.0 / bpm
    t = 0.2
    while t < duration_s:
        start = int(t * fs)
        length = int(min(decay_s * 4, duration_s - t) * fs)
        for k in range(length):
            if start + k >= n:
                break
            tau = k / fs
            out[start + k] += (
                amplitude * math.exp(-tau / decay_s) * math.sin(2 * math.pi * ring_hz * tau)
            )
        t += period
    return out


def noise(duration_s: float, fs: float, sigma: float, rng: random.Random) -> list[float]:
    return [rng.gauss(0.0, sigma) for _ in range(int(duration_s * fs))]


def motion_burst(
    signal: list[float], fs: float, at_s: float, duration_s: float, amplitude: float,
    rng: random.Random,
) -> list[float]:
    """Поворот во сне: короткий мощный широкополосный всплеск."""
    out = list(signal)
    start, end = int(at_s * fs), int((at_s + duration_s) * fs)
    for i in range(start, min(end, len(out))):
        out[i] += rng.gauss(0.0, amplitude)
    return out


def mix(*signals: list[float]) -> list[float]:
    n = min(len(s) for s in signals)
    return [sum(s[i] for s in signals) for i in range(n)]


def empty_bed(duration_s: float, fs: float, sigma: float, rng: random.Random) -> list[float]:
    """Пустая постель: только шум плёнки и наводка 50 Гц."""
    n = int(duration_s * fs)
    return [
        rng.gauss(0.0, sigma) + 0.3 * sigma * math.sin(2 * math.pi * 50.0 * i / fs)
        for i in range(n)
    ]
