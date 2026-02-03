"""Goal mapping and utility scoring for Hallar DSS."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np

from hallar.models import (
    GoalSet,
    WeightPreset,
    ComposedScenario,
    ComposedScenarioSet,
    GoalScores,
)
from hallar.simulation.monte_carlo import SimulationResults


@dataclass
class GoalMetrics:
    """Computed metrics for a single goal."""

    goal_id: str
    raw_value: float
    normalized_score: float  # 0-100
    weighted_contribution: float


@dataclass
class ScenarioGoalAnalysis:
    """Complete goal analysis for a scenario."""

    scenario_id: str
    metrics: Dict[str, GoalMetrics]
    total_utility: float
    rank: int = 0


def normalize_score(value: float, min_val: float, max_val: float, direction: str) -> float:
    """Normalize a value to 0-100 scale.

    Args:
        value: Raw value to normalize
        min_val: Minimum value in range
        max_val: Maximum value in range
        direction: 'maximize' or 'minimize'

    Returns:
        Normalized score 0-100 (higher is better)
    """
    if max_val == min_val:
        return 50.0

    normalized = (value - min_val) / (max_val - min_val)

    if direction == "minimize":
        normalized = 1 - normalized

    return max(0, min(100, normalized * 100))


def compute_goal_metrics_from_simulation(
    results: SimulationResults,
    goal_id: str,
    direction: str,
) -> Tuple[float, float]:
    """Compute raw value and normalized score from simulation results.

    Args:
        results: Simulation results
        goal_id: Goal identifier (G1-G6)
        direction: 'maximize' or 'minimize'

    Returns:
        Tuple of (raw_value, normalized_score)
    """
    # Map goal IDs to simulation metrics
    if goal_id == "G1":  # Speed
        raw_value = np.mean(results.first_units_months)
        # Normalize: 24 months best, 48 months worst
        normalized = normalize_score(raw_value, 24, 48, direction)
    elif goal_id == "G2":  # Affordability
        raw_value = np.mean(results.affordable_percentage) * 100
        # Already 0-100 scale
        normalized = raw_value if direction == "maximize" else 100 - raw_value
    elif goal_id == "G3":  # Quality
        raw_value = 100 - np.mean(results.defect_rate) * 100
        normalized = raw_value if direction == "maximize" else 100 - raw_value
    elif goal_id == "G4":  # Financial
        raw_value = np.mean(results.npv)
        # Normalize: -2000 to 10000 M ISK range
        normalized = normalize_score(raw_value, -2000, 10000, direction)
    elif goal_id == "G5":  # Risk
        raw_value = results.prob_negative * 100
        # Risk is probability of loss - lower is better
        normalized = normalize_score(raw_value, 0, 50, "minimize")
    elif goal_id == "G6":  # Control
        raw_value = np.mean(results.city_control) * 100
        normalized = raw_value if direction == "maximize" else 100 - raw_value
    else:
        raw_value = 50.0
        normalized = 50.0

    return raw_value, normalized


def compute_goal_metrics_from_scores(
    scores: GoalScores,
    goal_id: str,
) -> Tuple[float, float]:
    """Compute raw value and normalized score from pre-defined goal scores.

    Args:
        scores: Pre-defined goal scores
        goal_id: Goal identifier (G1-G6)

    Returns:
        Tuple of (raw_value, normalized_score)
    """
    score_map = {
        "G1": scores.speed,
        "G2": scores.affordability,
        "G3": scores.quality,
        "G4": scores.financial,
        "G5": scores.risk,
        "G6": scores.control,
    }
    score = score_map.get(goal_id, 50)
    return float(score), float(score)


def analyze_scenario_goals(
    scenario: ComposedScenario,
    goals: GoalSet,
    weights: Dict[str, float],
    simulation_results: Optional[SimulationResults] = None,
) -> ScenarioGoalAnalysis:
    """Analyze a scenario against all goals.

    Args:
        scenario: Composed scenario to analyze
        goals: Goal definitions
        weights: Goal weights (must sum to ~1.0)
        simulation_results: Optional simulation results for dynamic metrics

    Returns:
        ScenarioGoalAnalysis with all metrics
    """
    metrics = {}
    total_utility = 0.0

    for goal_id, goal in goals.goals.items():
        weight = weights.get(goal_id, 0.0)

        if simulation_results is not None:
            raw_value, normalized = compute_goal_metrics_from_simulation(
                simulation_results, goal_id, goal.direction.value
            )
        else:
            raw_value, normalized = compute_goal_metrics_from_scores(
                scenario.goal_scores, goal_id
            )

        weighted_contribution = normalized * weight
        total_utility += weighted_contribution

        metrics[goal_id] = GoalMetrics(
            goal_id=goal_id,
            raw_value=raw_value,
            normalized_score=normalized,
            weighted_contribution=weighted_contribution,
        )

    return ScenarioGoalAnalysis(
        scenario_id=scenario.id,
        metrics=metrics,
        total_utility=total_utility,
    )


def rank_scenarios_by_utility(
    scenarios: ComposedScenarioSet,
    goals: GoalSet,
    weights: Dict[str, float],
    simulation_results_map: Optional[Dict[str, SimulationResults]] = None,
) -> List[ScenarioGoalAnalysis]:
    """Rank all scenarios by total utility.

    Args:
        scenarios: Set of composed scenarios
        goals: Goal definitions
        weights: Goal weights
        simulation_results_map: Optional map of scenario_id -> SimulationResults

    Returns:
        List of analyses sorted by utility (highest first)
    """
    analyses = []

    for scenario_id, scenario in scenarios.scenarios.items():
        sim_results = None
        if simulation_results_map:
            sim_results = simulation_results_map.get(scenario_id)

        analysis = analyze_scenario_goals(scenario, goals, weights, sim_results)
        analyses.append(analysis)

    # Sort by utility descending
    analyses.sort(key=lambda a: a.total_utility, reverse=True)

    # Assign ranks
    for rank, analysis in enumerate(analyses, 1):
        analysis.rank = rank

    return analyses


def get_best_scenarios_for_goal(
    scenarios: ComposedScenarioSet,
    goal_id: str,
    top_n: int = 3,
) -> List[ComposedScenario]:
    """Get the best scenarios for a specific goal.

    Args:
        scenarios: Set of composed scenarios
        goal_id: Goal to optimize for
        top_n: Number of scenarios to return

    Returns:
        List of best scenarios for the goal
    """
    score_attr_map = {
        "G1": "speed",
        "G2": "affordability",
        "G3": "quality",
        "G4": "financial",
        "G5": "risk",
        "G6": "control",
    }
    attr = score_attr_map.get(goal_id, "speed")

    sorted_scenarios = sorted(
        scenarios.scenarios.values(),
        key=lambda s: getattr(s.goal_scores, attr),
        reverse=True,
    )

    return sorted_scenarios[:top_n]


def compute_pareto_front(
    scenarios: ComposedScenarioSet,
    goal_ids: List[str],
) -> List[ComposedScenario]:
    """Compute Pareto-optimal scenarios for given goals.

    Args:
        scenarios: Set of composed scenarios
        goal_ids: Goals to consider (all should be maximized)

    Returns:
        List of Pareto-optimal scenarios
    """
    score_attr_map = {
        "G1": "speed",
        "G2": "affordability",
        "G3": "quality",
        "G4": "financial",
        "G5": "risk",
        "G6": "control",
    }

    def get_scores(scenario: ComposedScenario) -> List[int]:
        return [
            getattr(scenario.goal_scores, score_attr_map[gid])
            for gid in goal_ids
        ]

    def dominates(scores_a: List[int], scores_b: List[int]) -> bool:
        """Return True if a dominates b (a >= b in all, a > b in at least one)."""
        at_least_one_better = False
        for a, b in zip(scores_a, scores_b):
            if a < b:
                return False
            if a > b:
                at_least_one_better = True
        return at_least_one_better

    pareto = []
    scenario_list = list(scenarios.scenarios.values())

    for scenario in scenario_list:
        scores = get_scores(scenario)
        is_dominated = False

        for other in scenario_list:
            if other.id != scenario.id:
                other_scores = get_scores(other)
                if dominates(other_scores, scores):
                    is_dominated = True
                    break

        if not is_dominated:
            pareto.append(scenario)

    return pareto
