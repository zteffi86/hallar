"""Multi-objective utility scoring for Hallar DSS."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class NormalizationParams:
    """Parameters for normalizing objective values to [0, 1]."""

    best: float  # Best value for this objective
    worst: float  # Worst value for this objective
    direction: str  # "maximize" or "minimize"

    def __post_init__(self) -> None:
        if self.direction not in ["maximize", "minimize"]:
            raise ValueError("direction must be 'maximize' or 'minimize'")

    def normalize(self, value: float) -> float:
        """
        Normalize a raw value to [0, 1] scale.

        For maximize objectives: higher raw value = higher normalized value
        For minimize objectives: lower raw value = higher normalized value

        Args:
            value: Raw metric value

        Returns:
            Normalized value in [0, 1]
        """
        if self.best == self.worst:
            return 0.5  # All values same, return midpoint

        if self.direction == "minimize":
            # Lower is better (e.g., time, cost)
            normalized = (self.worst - value) / (self.worst - self.best)
        else:
            # Higher is better (e.g., NPV, quality)
            normalized = (value - self.worst) / (self.best - self.worst)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, normalized))


# Default normalization parameters based on typical ranges
DEFAULT_NORMALIZATION = {
    "speed": NormalizationParams(
        best=36,    # 3 years is excellent
        worst=144,  # 12 years is very slow
        direction="minimize"
    ),
    "affordability": NormalizationParams(
        best=100,   # Maximum affordability score
        worst=0,    # No affordability commitment
        direction="maximize"
    ),
    "quality": NormalizationParams(
        best=100,   # Maximum quality score
        worst=0,    # Minimum quality
        direction="maximize"
    ),
    "financial": NormalizationParams(
        best=10000,   # Strong positive NPV
        worst=-5000,  # Significant loss
        direction="maximize"
    ),
}


def calculate_utility(
    metrics: Dict[str, float],
    weights: Dict[str, float],
    normalization_params: Dict[str, NormalizationParams] = None,
) -> float:
    """
    Calculate weighted additive utility score.

    U(s) = Σ w_i * u_i(x_i)

    Where:
    - w_i = weight for objective i (should sum to 1)
    - u_i = sub-utility function for objective i (normalized to [0,1])
    - x_i = raw metric value for objective i

    Args:
        metrics: Dict mapping objective names to raw values
        weights: Dict mapping objective names to weights (should sum to 1)
        normalization_params: Dict mapping objective names to NormalizationParams

    Returns:
        Utility score in [0, 1]
    """
    if normalization_params is None:
        normalization_params = DEFAULT_NORMALIZATION

    utility = 0.0
    total_weight = 0.0

    for objective, weight in weights.items():
        if objective not in metrics:
            continue

        raw_value = metrics[objective]
        params = normalization_params.get(objective)

        if params is None:
            # Default: assume maximize and use value directly if in [0,1]
            normalized = max(0.0, min(1.0, raw_value))
        else:
            normalized = params.normalize(raw_value)

        utility += weight * normalized
        total_weight += weight

    # Handle case where not all objectives have values
    if total_weight > 0 and total_weight < 1.0:
        utility = utility / total_weight

    return utility


def calculate_objective_metrics(
    simulation_results: Dict[str, Any],
    scenario: Any,
) -> Dict[str, float]:
    """
    Calculate objective metrics from simulation results.

    Objectives:
    - speed: Time to 60% completion (months)
    - affordability: Affordability score (0-100)
    - quality: Quality score (0-100)
    - financial: Expected NPV

    Args:
        simulation_results: Dict with simulation output arrays
        scenario: Scenario object with static parameters

    Returns:
        Dict mapping objective names to values
    """
    import numpy as np

    return {
        "speed": float(np.mean(simulation_results["sixty_percent_months"])),
        "affordability": float(np.mean(simulation_results["affordability_score"])),
        "quality": float(np.mean(simulation_results["quality_score"])),
        "financial": float(np.mean(simulation_results["npv"])),
    }


def update_normalization_from_results(
    all_results: list,
    normalization_params: Dict[str, NormalizationParams] = None,
) -> Dict[str, NormalizationParams]:
    """
    Update normalization parameters based on actual result ranges.

    This ensures normalization is relative to the scenarios being compared.

    Args:
        all_results: List of ScenarioResult objects
        normalization_params: Base parameters to update

    Returns:
        Updated normalization parameters
    """
    if normalization_params is None:
        normalization_params = {k: NormalizationParams(v.best, v.worst, v.direction)
                               for k, v in DEFAULT_NORMALIZATION.items()}

    # Collect all values for each objective
    values = {"speed": [], "affordability": [], "quality": [], "financial": []}

    for result in all_results:
        if hasattr(result, 'metrics'):
            metrics = result.metrics
            if "expected_time" in metrics:
                values["speed"].append(metrics["expected_time"])
            if "affordability_score" in metrics:
                values["affordability"].append(metrics["affordability_score"])
            if "quality_score" in metrics:
                values["quality"].append(metrics["quality_score"])
            if "expected_npv" in metrics:
                values["financial"].append(metrics["expected_npv"])

    # Update best/worst based on actual values with some padding
    for obj, vals in values.items():
        if vals:
            min_val = min(vals)
            max_val = max(vals)
            padding = (max_val - min_val) * 0.1 if max_val > min_val else abs(max_val) * 0.1

            if normalization_params[obj].direction == "minimize":
                normalization_params[obj] = NormalizationParams(
                    best=min_val - padding,
                    worst=max_val + padding,
                    direction="minimize"
                )
            else:
                normalization_params[obj] = NormalizationParams(
                    best=max_val + padding,
                    worst=min_val - padding,
                    direction="maximize"
                )

    return normalization_params
