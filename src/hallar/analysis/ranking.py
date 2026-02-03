"""Scenario ranking utilities for Hallar DSS."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from hallar.simulation.monte_carlo import ScenarioResult, FullAnalysisResults
    from hallar.models.weights import WeightProfile


@dataclass
class RankingResult:
    """Result of scenario ranking."""

    scenario_id: str
    scenario_name: str
    rank: int
    utility: float
    passed_constraints: bool
    metrics: Dict[str, float]


def rank_scenarios(
    results: "FullAnalysisResults",
    include_failed: bool = True,
) -> List[RankingResult]:
    """
    Rank scenarios by utility score.

    Args:
        results: Full analysis results
        include_failed: Whether to include scenarios that failed constraints

    Returns:
        List of RankingResult objects sorted by utility (highest first)
    """
    ranking = []

    for i, result in enumerate(results.ranked_results):
        if not include_failed and not result.passed_constraints:
            continue

        ranking.append(RankingResult(
            scenario_id=result.scenario.id,
            scenario_name=result.scenario.name,
            rank=i + 1,
            utility=result.utility,
            passed_constraints=result.passed_constraints,
            metrics=result.metrics.copy(),
        ))

    return ranking


def rank_by_weight_profiles(
    results: "FullAnalysisResults",
    weight_profiles: List["WeightProfile"],
) -> Dict[str, List[RankingResult]]:
    """
    Rank scenarios under different weight profiles.

    Args:
        results: Full analysis results
        weight_profiles: List of weight profiles to evaluate

    Returns:
        Dict mapping profile ID to list of rankings
    """
    from hallar.simulation.utility import calculate_utility

    rankings = {}

    for profile in weight_profiles:
        # Recalculate utilities with new weights
        scored_results = []
        for result in results.scenario_results:
            objective_metrics = {
                "speed": result.metrics["expected_time"],
                "affordability": result.metrics["affordability_score"],
                "quality": result.metrics["quality_score"],
                "financial": result.metrics["expected_npv"],
            }
            utility = calculate_utility(
                objective_metrics,
                profile.weights,
                results.normalization_params,
            )
            scored_results.append((result, utility))

        # Sort by utility
        scored_results.sort(key=lambda x: x[1], reverse=True)

        # Create ranking
        profile_ranking = []
        for rank, (result, utility) in enumerate(scored_results, 1):
            profile_ranking.append(RankingResult(
                scenario_id=result.scenario.id,
                scenario_name=result.scenario.name,
                rank=rank,
                utility=utility,
                passed_constraints=result.passed_constraints,
                metrics=result.metrics.copy(),
            ))

        rankings[profile.id] = profile_ranking

    return rankings


def get_winner_under_all_profiles(
    profile_rankings: Dict[str, List[RankingResult]],
    constraints_only: bool = True,
) -> Dict[str, int]:
    """
    Count how many times each scenario wins under different weight profiles.

    Args:
        profile_rankings: Rankings by profile from rank_by_weight_profiles
        constraints_only: Only consider scenarios that passed constraints

    Returns:
        Dict mapping scenario ID to win count
    """
    wins = {}

    for profile_id, ranking in profile_rankings.items():
        # Find winner (first that passed constraints if required)
        for result in ranking:
            if constraints_only and not result.passed_constraints:
                continue
            wins[result.scenario_id] = wins.get(result.scenario_id, 0) + 1
            break

    return wins


def identify_robust_scenarios(
    profile_rankings: Dict[str, List[RankingResult]],
    top_n: int = 3,
    constraints_only: bool = True,
) -> List[str]:
    """
    Identify scenarios that rank in top N across all weight profiles.

    These are "robust" scenarios that perform well regardless of priorities.

    Args:
        profile_rankings: Rankings by profile from rank_by_weight_profiles
        top_n: Consider scenarios in top N
        constraints_only: Only consider scenarios that passed constraints

    Returns:
        List of scenario IDs that are in top N under all profiles
    """
    all_profiles = list(profile_rankings.keys())
    if not all_profiles:
        return []

    # Get top N from first profile
    first_ranking = profile_rankings[all_profiles[0]]
    candidates = set()

    for result in first_ranking[:top_n * 2]:  # Consider more to handle constraint filtering
        if constraints_only and not result.passed_constraints:
            continue
        candidates.add(result.scenario_id)
        if len(candidates) >= top_n:
            break

    # Filter to those in top N for all profiles
    robust = []
    for scenario_id in candidates:
        is_robust = True
        for profile_id in all_profiles:
            ranking = profile_rankings[profile_id]
            # Find this scenario's rank
            count = 0
            found_in_top_n = False
            for result in ranking:
                if constraints_only and not result.passed_constraints:
                    continue
                count += 1
                if result.scenario_id == scenario_id:
                    if count <= top_n:
                        found_in_top_n = True
                    break
                if count >= top_n:
                    break

            if not found_in_top_n:
                is_robust = False
                break

        if is_robust:
            robust.append(scenario_id)

    return robust
