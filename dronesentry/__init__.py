"""DroneSentry — бортовой модуль обнаружения дронов для DJI Mavic.

Всё измеряется относительно носителя, а не оператора. Покрытие по классам
целей и физические границы метода описаны в README.md этого пакета.
"""

from .geo import Fix
from .fusion import Alert, Tracker
from .targets import Detection, Source, TargetClass, Track

__all__ = ["Fix", "Alert", "Tracker", "Detection", "Source", "TargetClass", "Track"]
