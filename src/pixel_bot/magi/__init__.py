"""MAGI deliberative governance for Pixel Bot.

MAGI evaluates development proposals through three independent perspectives:
Melchior (technical evolution), Balthasar (protection and risk), and Caspar
(strategic perseverance).
"""

from .council import MagiCouncil
from .models import DecisionStatus, MagiDecision, MagiOpinion, MagiProposal, MagiRole

__all__ = [
    "DecisionStatus",
    "MagiCouncil",
    "MagiDecision",
    "MagiOpinion",
    "MagiProposal",
    "MagiRole",
]
