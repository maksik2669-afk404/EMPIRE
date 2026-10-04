"""Центр принятий решений: локальный, автономный, объяснимый.

Решения принимаются на месте — сеть нужна только чтобы отправить готовое
сообщение. Каждая тревога печатает слагаемые, из которых она сложилась.
"""

from .air import AirMonitor, AirReading
from .model import ASK_THRESHOLD, PRIOR_LOG_ODDS, WEIGHTS, Assessment, DecisionCenter
from .signals import Observation, Signal
from .system import Act, Decision, HomeSystem

__all__ = [
    "AirMonitor", "AirReading", "Assessment", "DecisionCenter", "Observation",
    "Signal", "Act", "Decision", "HomeSystem", "WEIGHTS", "ASK_THRESHOLD",
    "PRIOR_LOG_ODDS",
]
