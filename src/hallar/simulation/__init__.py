"""Simulation engine for Hallar DSS."""

from hallar.simulation.distributions import pert_distribution, pert_sample, triangular_sample
from hallar.simulation.npv import calculate_npv, calculate_risk_adjusted_npv
from hallar.simulation.utility import calculate_utility, NormalizationParams
from hallar.simulation.monte_carlo import (
    MonteCarloSimulation,
    SimulationResults,
    ScenarioResult,
    FullAnalysisResults,
    run_simulation,
    run_full_analysis,
)

# New composed scenario support
from hallar.simulation.composed_runner import (
    ComposedScenarioRunner,
    ComponentRegistry,
    ComposedSimulationConfig,
    run_composed_analysis,
    GoalMetricResult,
    ScenarioGoalAnalysis,
    compute_goal_metrics,
    rank_scenarios_by_utility,
)

__all__ = [
    # Distributions
    "pert_distribution",
    "pert_sample",
    "triangular_sample",
    # NPV
    "calculate_npv",
    "calculate_risk_adjusted_npv",
    # Utility
    "calculate_utility",
    "NormalizationParams",
    # Monte Carlo
    "MonteCarloSimulation",
    "SimulationResults",
    "ScenarioResult",
    "FullAnalysisResults",
    "run_simulation",
    "run_full_analysis",
    # Composed scenario support
    "ComposedScenarioRunner",
    "ComponentRegistry",
    "ComposedSimulationConfig",
    "run_composed_analysis",
    "GoalMetricResult",
    "ScenarioGoalAnalysis",
    "compute_goal_metrics",
    "rank_scenarios_by_utility",
]
