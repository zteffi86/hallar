"""Pareto dominance analysis for Hallar DSS."""

from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from hallar.simulation.monte_carlo import ScenarioResult, FullAnalysisResults


@dataclass
class DominanceResult:
    """Result of dominance analysis for a scenario."""

    scenario_id: str
    scenario_name: str
    is_pareto_optimal: bool
    dominated_by: List[str]  # Scenario IDs that dominate this one
    dominates: List[str]  # Scenario IDs dominated by this one
    objectives: Dict[str, float]


def find_pareto_frontier(
    results: "FullAnalysisResults",
    objectives: Optional[List[str]] = None,
    constraints_only: bool = True,
) -> List[DominanceResult]:
    """
    Find Pareto-optimal scenarios.

    A scenario is Pareto-optimal if no other scenario is better in all objectives.

    Args:
        results: Full analysis results
        objectives: Objectives to consider (default: speed, affordability, quality, financial)
        constraints_only: Only consider scenarios that passed constraints

    Returns:
        List of DominanceResult for all scenarios
    """
    if objectives is None:
        objectives = ["speed", "affordability", "quality", "financial"]

    # Build objective values for each scenario
    # Note: speed is "minimize" (lower is better), others are "maximize"
    scenario_objectives = {}

    for result in results.scenario_results:
        if constraints_only and not result.passed_constraints:
            continue

        # Normalize direction: higher is better for all
        obj_values = {}
        for obj in objectives:
            if obj == "speed":
                # Convert to "lower is better" -> negate so higher is better
                obj_values[obj] = -result.metrics.get("expected_time", 0)
            elif obj == "affordability":
                obj_values[obj] = result.metrics.get("affordability_score", 0)
            elif obj == "quality":
                obj_values[obj] = result.metrics.get("quality_score", 0)
            elif obj == "financial":
                obj_values[obj] = result.metrics.get("expected_npv", 0)
            else:
                obj_values[obj] = result.metrics.get(obj, 0)

        scenario_objectives[result.scenario.id] = {
            "name": result.scenario.name,
            "values": obj_values,
        }

    # Find dominance relationships
    dominance_results = []

    for sid, sdata in scenario_objectives.items():
        dominated_by = []
        dominates = []

        for other_id, other_data in scenario_objectives.items():
            if sid == other_id:
                continue

            # Check if other dominates this
            if _dominates(other_data["values"], sdata["values"], objectives):
                dominated_by.append(other_id)

            # Check if this dominates other
            if _dominates(sdata["values"], other_data["values"], objectives):
                dominates.append(other_id)

        dominance_results.append(DominanceResult(
            scenario_id=sid,
            scenario_name=sdata["name"],
            is_pareto_optimal=len(dominated_by) == 0,
            dominated_by=dominated_by,
            dominates=dominates,
            objectives={obj: sdata["values"][obj] for obj in objectives},
        ))

    # Sort: Pareto-optimal first, then by number of scenarios dominated
    dominance_results.sort(
        key=lambda r: (-int(r.is_pareto_optimal), -len(r.dominates))
    )

    return dominance_results


def _dominates(a: Dict[str, float], b: Dict[str, float], objectives: List[str]) -> bool:
    """
    Check if scenario A dominates scenario B.

    A dominates B if A is at least as good in all objectives and strictly better in at least one.
    (Assumes higher is better for all objectives after normalization)
    """
    at_least_as_good = True
    strictly_better = False

    for obj in objectives:
        if a[obj] < b[obj]:
            at_least_as_good = False
            break
        if a[obj] > b[obj]:
            strictly_better = True

    return at_least_as_good and strictly_better


def get_pareto_frontier_scenarios(
    results: "FullAnalysisResults",
    constraints_only: bool = True,
) -> List[str]:
    """
    Get list of Pareto-optimal scenario IDs.

    Args:
        results: Full analysis results
        constraints_only: Only consider scenarios that passed constraints

    Returns:
        List of scenario IDs on the Pareto frontier
    """
    dominance = find_pareto_frontier(results, constraints_only=constraints_only)
    return [d.scenario_id for d in dominance if d.is_pareto_optimal]


def pairwise_comparison(
    results: "FullAnalysisResults",
    scenario_a: str,
    scenario_b: str,
) -> Dict[str, Any]:
    """
    Compare two scenarios head-to-head.

    Args:
        results: Full analysis results
        scenario_a: First scenario ID
        scenario_b: Second scenario ID

    Returns:
        Dict with comparison details
    """
    result_a = None
    result_b = None

    for r in results.scenario_results:
        if r.scenario.id == scenario_a:
            result_a = r
        if r.scenario.id == scenario_b:
            result_b = r

    if result_a is None or result_b is None:
        raise ValueError(f"Scenario not found: {scenario_a if result_a is None else scenario_b}")

    comparison = {
        "scenario_a": scenario_a,
        "scenario_b": scenario_b,
        "objectives": {},
        "winner_by_objective": {},
        "overall_winner": None,
    }

    objectives = {
        "speed": ("expected_time", "minimize"),
        "affordability": ("affordability_score", "maximize"),
        "quality": ("quality_score", "maximize"),
        "financial": ("expected_npv", "maximize"),
    }

    a_wins = 0
    b_wins = 0

    for obj_name, (metric, direction) in objectives.items():
        val_a = result_a.metrics.get(metric, 0)
        val_b = result_b.metrics.get(metric, 0)

        comparison["objectives"][obj_name] = {
            "a": val_a,
            "b": val_b,
            "difference": val_a - val_b,
        }

        if direction == "maximize":
            winner = "a" if val_a > val_b else ("b" if val_b > val_a else "tie")
        else:
            winner = "a" if val_a < val_b else ("b" if val_b < val_a else "tie")

        comparison["winner_by_objective"][obj_name] = winner

        if winner == "a":
            a_wins += 1
        elif winner == "b":
            b_wins += 1

    # Determine overall winner based on utility
    if result_a.utility > result_b.utility:
        comparison["overall_winner"] = "a"
    elif result_b.utility > result_a.utility:
        comparison["overall_winner"] = "b"
    else:
        comparison["overall_winner"] = "tie"

    comparison["utility_a"] = result_a.utility
    comparison["utility_b"] = result_b.utility
    comparison["objectives_won_a"] = a_wins
    comparison["objectives_won_b"] = b_wins

    return comparison
