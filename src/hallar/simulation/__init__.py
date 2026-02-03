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

__all__ = [
    "pert_distribution",
    "pert_sample",
    "triangular_sample",
    "calculate_npv",
    "calculate_risk_adjusted_npv",
    "calculate_utility",
    "NormalizationParams",
    "MonteCarloSimulation",
    "SimulationResults",
    "ScenarioResult",
    "FullAnalysisResults",
    "run_simulation",
    "run_full_analysis",
]
