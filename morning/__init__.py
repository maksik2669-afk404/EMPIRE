"""«Утро» — датчик под матрасом и утренняя сводка родне.

Продукт — не прибор, а сообщение, которое приходит каждое утро. Техника
спрятана: плёнка PVDF даёт дыхание и пульс, тензодатчики под ножками кровати
дают факт присутствия, число людей в постели и вес.
"""

from .digest import render
from .dsp import WindowResult, analyze_window
from .night import NightRecorder, NightSummary, RespGapEpisode
from .presence import BedFusion, BedState, LoadReading

__all__ = [
    "render", "WindowResult", "analyze_window", "NightRecorder", "NightSummary",
    "RespGapEpisode", "BedFusion", "BedState", "LoadReading",
]
