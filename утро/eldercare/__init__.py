"""Eldercare — стационарное устройство связи и контроля для пожилого человека.

Пожилой человек получает одну кнопку и голосовую связь с роднёй. Контроль
распорядка возникает побочным продуктом. Перед любой тревогой устройство
спрашивает самого человека — это и убивает ложные тревоги, и оставляет
решение за ним.
"""

from .baseline import Baseline, learn_from_history
from .detector import Detector, FamilyAlert, Prompt, Rule, Severity
from .events import Event, EventKind, VitalsSource, Zone

__all__ = [
    "Baseline", "learn_from_history", "Detector", "FamilyAlert", "Prompt",
    "Rule", "Severity", "Event", "EventKind", "VitalsSource", "Zone",
]
