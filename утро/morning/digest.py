"""Утренняя сводка — сам продукт.

Это не отчёт прибора, а сообщение, которое родственник читает за кофе. Поэтому
формулировки человеческие, а числа появляются только там, где они что-то
значат. Никаких диагнозов: «дыхание не регистрировалось» — состояние датчика,
а не клинический вывод.
"""
from __future__ import annotations

from datetime import timedelta

from .night import NightSummary

_WEIGHT_ALERT_KG = 2.0


def _hm(td: timedelta) -> str:
    total = int(td.total_seconds() // 60)
    return f"{total // 60} ч {total % 60:02d} мин"


def _plural(n: int, one: str, few: str, many: str) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return one
    if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
        return few
    return many


def render(
    s: NightSummary, name: str = "мама", weight_baseline_kg: float | None = None
) -> str:
    """Текст для Telegram. Первая строка должна отвечать на главный вопрос."""
    lines: list[str] = []

    if s.alarms:
        worst = max(s.alarms, key=lambda e: e.duration)
        lines.append(
            f"⚠️ Ночью дыхание не регистрировалось {int(worst.duration.total_seconds() // 60)} мин "
            f"в {worst.start:%H:%M}, при этом {name} была в постели и не двигалась. "
            f"Стоит позвонить."
        )
        lines.append("")
    elif s.in_bed_from is None:
        lines.append(f"Доброе утро. В постели {name} этой ночью не было.")
        return "\n".join(lines)
    else:
        lines.append(f"Доброе утро. Ночь прошла спокойно.")

    if s.in_bed_from and s.in_bed_to:
        lines.append(f"Легла в {s.in_bed_from:%H:%M}, встала в {s.in_bed_to:%H:%M}.")
    lines.append(f"В постели {_hm(s.time_in_bed)}.")

    if s.awakenings:
        word = _plural(s.awakenings, "раз", "раза", "раз")
        lines.append(f"Вставала {s.awakenings} {word}.")
    else:
        lines.append("Ночью не вставала.")

    if s.resp_bpm_median is not None:
        lines.append(f"Дыхание ровное, {s.resp_bpm_median:.0f} в минуту.")
    if s.hr_bpm_median is not None:
        lines.append(f"Пульс во сне {s.hr_bpm_median:.0f}.")
    elif s.two_in_bed_minutes > 30:
        lines.append("Пульс не измерялся: в постели были двое.")

    if s.weight_kg is not None:
        if weight_baseline_kg is not None:
            delta = s.weight_kg - weight_baseline_kg
            if abs(delta) >= _WEIGHT_ALERT_KG:
                sign = "больше" if delta > 0 else "меньше"
                lines.append(
                    f"Вес {s.weight_kg:.1f} кг — на {abs(delta):.1f} кг {sign}, "
                    f"чем обычно. Если так несколько дней подряд, скажите врачу."
                )
            else:
                lines.append(f"Вес {s.weight_kg:.1f} кг, как обычно.")
        else:
            lines.append(f"Вес {s.weight_kg:.1f} кг.")

    # Перерыв при пустой кровати — это подъём, он уже в строке «вставала».
    # Сообщаем только о перерывах, случившихся в постели: это, скорее всего,
    # потеря контакта датчика, и об этом полезно знать.
    dropouts = [
        e for e in s.resp_gaps
        if not e.corroborated and e.in_bed and e.duration >= timedelta(minutes=3)
    ]
    if dropouts and not s.alarms:
        word = _plural(len(dropouts), "перерыв", "перерыва", "перерывов")
        lines.append(
            f"Было {len(dropouts)} {word} в сигнале, когда {name} была в постели — "
            f"возможно, датчик сдвинулся. Если повторится, поправьте плёнку."
        )
    return "\n".join(lines)
