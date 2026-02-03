"""
Hallar Decision Support System

A quantitative decision support system for comparing land development scenarios.
"""

__version__ = "0.1.0"

from hallar.models.scenario import Scenario, PERTParams, RiskParams, AffordabilityParams, QualityParams, JVParams
from hallar.models.market import MarketScenario
from hallar.models.constraints import Constraint, ConstraintSet
from hallar.models.weights import WeightProfile

from hallar.simulation.monte_carlo import MonteCarloSimulation, SimulationResults
from hallar.simulation.npv import calculate_npv, calculate_risk_adjusted_npv
from hallar.simulation.distributions import pert_distribution, pert_sample

from hallar.io.loaders import load_scenarios, load_markets, load_constraints, load_weights
from hallar.io.exporters import export_to_excel, export_to_json

from hallar.analysis.ranking import rank_scenarios
from hallar.analysis.sensitivity import sensitivity_analysis
from hallar.analysis.dominance import find_pareto_frontier

__all__ = [
    # Models
    "Scenario",
    "PERTParams",
    "RiskParams",
    "AffordabilityParams",
    "QualityParams",
    "JVParams",
    "MarketScenario",
    "Constraint",
    "ConstraintSet",
    "WeightProfile",
    # Simulation
    "MonteCarloSimulation",
    "SimulationResults",
    "calculate_npv",
    "calculate_risk_adjusted_npv",
    "pert_distribution",
    "pert_sample",
    # IO
    "load_scenarios",
    "load_markets",
    "load_constraints",
    "load_weights",
    "export_to_excel",
    "export_to_json",
    # Analysis
    "rank_scenarios",
    "sensitivity_analysis",
    "find_pareto_frontier",
]
