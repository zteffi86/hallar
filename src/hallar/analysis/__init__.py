"""Analysis tools for Hallar DSS."""

from hallar.analysis.ranking import rank_scenarios, RankingResult
from hallar.analysis.sensitivity import sensitivity_analysis, SensitivityResult
from hallar.analysis.dominance import find_pareto_frontier, DominanceResult

__all__ = [
    "rank_scenarios",
    "RankingResult",
    "sensitivity_analysis",
    "SensitivityResult",
    "find_pareto_frontier",
    "DominanceResult",
]
