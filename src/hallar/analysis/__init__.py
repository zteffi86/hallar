"""Analysis tools for Hallar DSS."""

from hallar.analysis.ranking import rank_scenarios, RankingResult
from hallar.analysis.sensitivity import sensitivity_analysis, SensitivityResult
from hallar.analysis.dominance import find_pareto_frontier, DominanceResult

# New analysis modules
from hallar.analysis.goal_mapping import (
    GoalMetrics,
    ScenarioGoalAnalysis,
    normalize_score,
    analyze_scenario_goals,
    rank_scenarios_by_utility,
    get_best_scenarios_for_goal,
    compute_pareto_front,
)
from hallar.analysis.risk_analysis import (
    RiskAssessment,
    CounterpartyRiskAssessment,
    ScenarioRiskProfile,
    assess_counterparty_risk,
    assess_risk,
    analyze_scenario_risks,
    compare_scenario_risks,
    simulate_risk_scenarios,
    calculate_var_cvar,
)
from hallar.analysis.constraint_checker import (
    ConstraintStatus,
    ConstraintDefinition,
    ConstraintResult,
    ScenarioConstraintResults,
    check_constraint_deterministic,
    check_constraint_probabilistic,
    check_scenario_constraints,
    filter_feasible_scenarios,
    DEFAULT_HALLAR_CONSTRAINTS,
)
from hallar.analysis.structure_composer import (
    CompatibilityIssue,
    CompositionValidation,
    validate_composition,
    estimate_goal_scores,
    compose_scenario,
    generate_all_valid_combinations,
    find_scenarios_matching_criteria,
)

__all__ = [
    # Original
    "rank_scenarios",
    "RankingResult",
    "sensitivity_analysis",
    "SensitivityResult",
    "find_pareto_frontier",
    "DominanceResult",
    # Goal mapping
    "GoalMetrics",
    "ScenarioGoalAnalysis",
    "normalize_score",
    "analyze_scenario_goals",
    "rank_scenarios_by_utility",
    "get_best_scenarios_for_goal",
    "compute_pareto_front",
    # Risk analysis
    "RiskAssessment",
    "CounterpartyRiskAssessment",
    "ScenarioRiskProfile",
    "assess_counterparty_risk",
    "assess_risk",
    "analyze_scenario_risks",
    "compare_scenario_risks",
    "simulate_risk_scenarios",
    "calculate_var_cvar",
    # Constraint checker
    "ConstraintStatus",
    "ConstraintDefinition",
    "ConstraintResult",
    "ScenarioConstraintResults",
    "check_constraint_deterministic",
    "check_constraint_probabilistic",
    "check_scenario_constraints",
    "filter_feasible_scenarios",
    "DEFAULT_HALLAR_CONSTRAINTS",
    # Structure composer
    "CompatibilityIssue",
    "CompositionValidation",
    "validate_composition",
    "estimate_goal_scores",
    "compose_scenario",
    "generate_all_valid_combinations",
    "find_scenarios_matching_criteria",
]
