"""Sensitivity analysis for Hallar DSS."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from hallar.models.scenario import Scenario
    from hallar.models.market import MarketScenario
    from hallar.simulation.monte_carlo import SimulationResults


@dataclass
class SensitivityResult:
    """Result of sensitivity analysis for a single parameter."""

    parameter: str
    base_value: float
    low_value: float
    high_value: float
    base_npv: float
    low_npv: float
    high_npv: float
    npv_swing: float  # high_npv - low_npv
    elasticity: float  # % change in NPV / % change in parameter


def sensitivity_analysis(
    scenario: "Scenario",
    market: "MarketScenario",
    base_results: "SimulationResults",
    parameters: Optional[List[str]] = None,
    variation: float = 0.20,
    n_simulations: int = 1000,
    random_seed: int = 42,
) -> List[SensitivityResult]:
    """
    Perform one-at-a-time sensitivity analysis.

    For each parameter, vary by ±variation and measure impact on expected NPV.

    Args:
        scenario: Base scenario
        market: Market condition
        base_results: Simulation results at base parameters
        parameters: List of parameters to analyze (None = all)
        variation: Fractional variation (e.g., 0.20 = ±20%)
        n_simulations: Simulations per variation
        random_seed: Random seed

    Returns:
        List of SensitivityResult sorted by NPV swing (highest first)
    """
    from hallar.simulation.monte_carlo import MonteCarloSimulation
    from hallar.models.scenario import Scenario, PERTParams
    import copy

    if parameters is None:
        parameters = [
            "infrastructure_cost",
            "rights_revenue",
            "cost_overrun_probability",
            "delay_probability",
            "developer_default_probability",
            "construction_cost_multiplier",
            "interest_rate",
            "property_price_growth",
        ]

    engine = MonteCarloSimulation(n_simulations=n_simulations, random_seed=random_seed)
    base_npv = float(np.mean(base_results.npv))

    results = []

    for param in parameters:
        # Get base value
        base_val, low_scenario, high_scenario, low_market, high_market = _create_variations(
            scenario, market, param, variation
        )

        if base_val is None:
            continue

        low_val = base_val * (1 - variation)
        high_val = base_val * (1 + variation)

        # Run simulations
        if low_scenario is not None:
            low_results = engine.run_scenario(low_scenario, market)
        else:
            low_results = engine.run_scenario(scenario, low_market)

        if high_scenario is not None:
            high_results = engine.run_scenario(high_scenario, market)
        else:
            high_results = engine.run_scenario(scenario, high_market)

        low_npv = float(np.mean(low_results.npv))
        high_npv = float(np.mean(high_results.npv))
        npv_swing = high_npv - low_npv

        # Calculate elasticity
        if abs(base_val) > 1e-10 and abs(base_npv) > 1e-10:
            pct_change_param = (high_val - low_val) / base_val
            pct_change_npv = (high_npv - low_npv) / abs(base_npv)
            elasticity = pct_change_npv / pct_change_param if pct_change_param != 0 else 0
        else:
            elasticity = 0

        results.append(SensitivityResult(
            parameter=param,
            base_value=base_val,
            low_value=low_val,
            high_value=high_val,
            base_npv=base_npv,
            low_npv=low_npv,
            high_npv=high_npv,
            npv_swing=abs(npv_swing),
            elasticity=elasticity,
        ))

    # Sort by swing (largest first)
    results.sort(key=lambda r: r.npv_swing, reverse=True)

    return results


def _create_variations(
    scenario: "Scenario",
    market: "MarketScenario",
    param: str,
    variation: float,
) -> Tuple[Optional[float], Optional["Scenario"], Optional["Scenario"],
           Optional["MarketScenario"], Optional["MarketScenario"]]:
    """Create low and high variations of scenario/market for a parameter."""
    import copy

    low_scenario = None
    high_scenario = None
    low_market = None
    high_market = None
    base_val = None

    # Scenario parameters
    if param == "infrastructure_cost":
        base_val = scenario.infrastructure_cost.likely
        low_scenario = copy.deepcopy(scenario)
        high_scenario = copy.deepcopy(scenario)
        low_scenario.infrastructure_cost = _scale_pert(scenario.infrastructure_cost, 1 - variation)
        high_scenario.infrastructure_cost = _scale_pert(scenario.infrastructure_cost, 1 + variation)

    elif param == "rights_revenue":
        base_val = scenario.rights_revenue.likely
        low_scenario = copy.deepcopy(scenario)
        high_scenario = copy.deepcopy(scenario)
        low_scenario.rights_revenue = _scale_pert(scenario.rights_revenue, 1 - variation)
        high_scenario.rights_revenue = _scale_pert(scenario.rights_revenue, 1 + variation)

    elif param == "cost_overrun_probability":
        base_val = scenario.risks.cost_overrun_probability
        low_scenario = copy.deepcopy(scenario)
        high_scenario = copy.deepcopy(scenario)
        low_scenario.risks.cost_overrun_probability = max(0, base_val * (1 - variation))
        high_scenario.risks.cost_overrun_probability = min(1, base_val * (1 + variation))

    elif param == "delay_probability":
        base_val = scenario.risks.delay_probability
        low_scenario = copy.deepcopy(scenario)
        high_scenario = copy.deepcopy(scenario)
        low_scenario.risks.delay_probability = max(0, base_val * (1 - variation))
        high_scenario.risks.delay_probability = min(1, base_val * (1 + variation))

    elif param == "developer_default_probability":
        base_val = scenario.risks.developer_default_probability
        if base_val == 0:
            return None, None, None, None, None
        low_scenario = copy.deepcopy(scenario)
        high_scenario = copy.deepcopy(scenario)
        low_scenario.risks.developer_default_probability = max(0, base_val * (1 - variation))
        high_scenario.risks.developer_default_probability = min(1, base_val * (1 + variation))

    # Market parameters
    elif param == "construction_cost_multiplier":
        base_val = market.parameters.construction_cost_multiplier
        low_market = copy.deepcopy(market)
        high_market = copy.deepcopy(market)
        low_market.parameters.construction_cost_multiplier = base_val * (1 - variation)
        high_market.parameters.construction_cost_multiplier = base_val * (1 + variation)

    elif param == "interest_rate":
        base_val = market.parameters.interest_rate
        low_market = copy.deepcopy(market)
        high_market = copy.deepcopy(market)
        low_market.parameters.interest_rate = max(0.01, base_val * (1 - variation))
        high_market.parameters.interest_rate = base_val * (1 + variation)

    elif param == "property_price_growth":
        base_val = market.parameters.property_price_growth
        low_market = copy.deepcopy(market)
        high_market = copy.deepcopy(market)
        low_market.parameters.property_price_growth = base_val - variation
        high_market.parameters.property_price_growth = base_val + variation

    return base_val, low_scenario, high_scenario, low_market, high_market


def _scale_pert(pert, factor: float):
    """Scale PERT distribution parameters by a factor."""
    from hallar.models.scenario import PERTParams
    return PERTParams(
        min=pert.min * factor,
        likely=pert.likely * factor,
        max=pert.max * factor,
    )


def weight_sensitivity_analysis(
    results: Any,
    weight_variations: int = 11,
) -> Dict[str, Dict[str, float]]:
    """
    Analyze how scenario rankings change with weight variations.

    Args:
        results: FullAnalysisResults
        weight_variations: Number of weight points to evaluate per objective

    Returns:
        Dict mapping weight profile description to scenario utilities
    """
    from hallar.simulation.utility import calculate_utility

    objectives = ["speed", "affordability", "quality", "financial"]
    weight_sensitivity = {}

    # Vary each objective from 0 to 1 while keeping others equal
    for primary_obj in objectives:
        for primary_weight in np.linspace(0.1, 0.7, weight_variations):
            # Distribute remaining weight equally among others
            remaining = 1 - primary_weight
            other_weight = remaining / 3

            weights = {obj: other_weight for obj in objectives}
            weights[primary_obj] = primary_weight

            # Calculate utilities
            profile_name = f"{primary_obj}={primary_weight:.2f}"
            weight_sensitivity[profile_name] = {}

            for result in results.scenario_results:
                objective_metrics = {
                    "speed": result.metrics["expected_time"],
                    "affordability": result.metrics["affordability_score"],
                    "quality": result.metrics["quality_score"],
                    "financial": result.metrics["expected_npv"],
                }
                utility = calculate_utility(
                    objective_metrics,
                    weights,
                    results.normalization_params,
                )
                weight_sensitivity[profile_name][result.scenario.id] = utility

    return weight_sensitivity
