"""Constraint checking module for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import numpy as np

from hallar.models import ComposedScenario, ComposedScenarioSet, PERTParams
from hallar.simulation.monte_carlo import SimulationResults


class ConstraintStatus(Enum):
    """Status of a constraint check."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    UNKNOWN = "unknown"


@dataclass
class ConstraintDefinition:
    """Definition of a constraint."""

    id: str
    name: str
    name_is: str
    description: str
    constraint_type: str  # "hard" or "soft"
    category: str  # "affordability", "timeline", "financial", "regulatory"
    metric: str  # What to measure
    operator: str  # ">=", "<=", "==", "between"
    threshold: Any  # Single value or dict for "between"
    probability_threshold: float = 0.95  # Required probability to pass

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "ConstraintDefinition":
        """Create ConstraintDefinition from a dictionary."""
        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            constraint_type=data.get("type", "hard"),
            category=data.get("category", "other"),
            metric=data["metric"],
            operator=data["operator"],
            threshold=data["threshold"],
            probability_threshold=data.get("probability_threshold", 0.95),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "type": self.constraint_type,
            "category": self.category,
            "metric": self.metric,
            "operator": self.operator,
            "threshold": self.threshold,
            "probability_threshold": self.probability_threshold,
        }


@dataclass
class ConstraintResult:
    """Result of checking a single constraint."""

    constraint_id: str
    constraint_name: str
    status: ConstraintStatus
    actual_value: float
    threshold_value: Any
    probability_met: float  # Probability that constraint is satisfied
    message: str


@dataclass
class ScenarioConstraintResults:
    """Results of checking all constraints for a scenario."""

    scenario_id: str
    scenario_name: str
    results: List[ConstraintResult]
    all_hard_constraints_pass: bool
    total_constraints: int
    passed_constraints: int
    warning_constraints: int
    failed_constraints: int


def check_constraint_deterministic(
    constraint: ConstraintDefinition,
    value: float,
) -> ConstraintResult:
    """Check a constraint against a deterministic value.

    Args:
        constraint: Constraint definition
        value: Value to check

    Returns:
        ConstraintResult
    """
    threshold = constraint.threshold
    operator = constraint.operator

    if operator == ">=":
        passes = value >= threshold
    elif operator == "<=":
        passes = value <= threshold
    elif operator == "==":
        passes = abs(value - threshold) < 0.001
    elif operator == "between":
        passes = threshold["min"] <= value <= threshold["max"]
    else:
        passes = True

    status = ConstraintStatus.PASS if passes else ConstraintStatus.FAIL

    return ConstraintResult(
        constraint_id=constraint.id,
        constraint_name=constraint.name,
        status=status,
        actual_value=value,
        threshold_value=threshold,
        probability_met=1.0 if passes else 0.0,
        message=f"{'Passed' if passes else 'Failed'}: {constraint.description}",
    )


def check_constraint_probabilistic(
    constraint: ConstraintDefinition,
    values: np.ndarray,
) -> ConstraintResult:
    """Check a constraint against an array of simulation values.

    Args:
        constraint: Constraint definition
        values: Array of simulated values

    Returns:
        ConstraintResult with probability-based assessment
    """
    threshold = constraint.threshold
    operator = constraint.operator

    if operator == ">=":
        satisfies = values >= threshold
    elif operator == "<=":
        satisfies = values <= threshold
    elif operator == "==":
        satisfies = np.abs(values - threshold) < 0.001
    elif operator == "between":
        satisfies = (values >= threshold["min"]) & (values <= threshold["max"])
    else:
        satisfies = np.ones(len(values), dtype=bool)

    probability_met = np.mean(satisfies)
    actual_value = np.mean(values)

    # Determine status
    if probability_met >= constraint.probability_threshold:
        status = ConstraintStatus.PASS
    elif probability_met >= constraint.probability_threshold - 0.1:
        status = ConstraintStatus.WARNING
    else:
        status = ConstraintStatus.FAIL

    return ConstraintResult(
        constraint_id=constraint.id,
        constraint_name=constraint.name,
        status=status,
        actual_value=actual_value,
        threshold_value=threshold,
        probability_met=probability_met,
        message=f"P({constraint.metric} {operator} {threshold}) = {probability_met:.1%}",
    )


def get_metric_value(
    scenario: ComposedScenario,
    metric: str,
) -> Optional[float]:
    """Extract a metric value from a composed scenario.

    Args:
        scenario: Composed scenario
        metric: Metric name

    Returns:
        Metric value or None if not found
    """
    # Handle goal score metrics
    if metric == "affordability_percentage":
        if scenario.affordability_commitment:
            return scenario.affordability_commitment.minimum_pct
        return 0.0
    elif metric == "city_control":
        return scenario.city_control_score / 100.0
    elif metric == "default_probability":
        return scenario.get_default_probability_likely()
    elif metric == "rental_percentage":
        if scenario.affordability_commitment:
            return scenario.affordability_commitment.rental_pct
        return 0.0
    elif metric == "city_equity_share":
        if scenario.equity_structure:
            return scenario.equity_structure.city_share
        return 0.0
    elif metric.startswith("goal_"):
        goal_name = metric.replace("goal_", "")
        return getattr(scenario.goal_scores, goal_name, None)

    return None


def get_metric_from_simulation(
    results: SimulationResults,
    metric: str,
) -> Optional[np.ndarray]:
    """Extract a metric array from simulation results.

    Args:
        results: Simulation results
        metric: Metric name

    Returns:
        Array of values or None if not found
    """
    metric_map = {
        "npv": results.npv,
        "first_units_months": results.first_units_months,
        "sixty_percent_months": results.sixty_percent_months,
        "affordable_percentage": results.affordable_percentage,
        "defect_rate": results.defect_rate,
        "city_control": results.city_control,
        "prob_negative": np.array([results.prob_negative] * len(results.npv)),
        "cvar_05": np.array([results.cvar_05] * len(results.npv)),
    }
    return metric_map.get(metric)


def check_scenario_constraints(
    scenario: ComposedScenario,
    constraints: List[ConstraintDefinition],
    simulation_results: Optional[SimulationResults] = None,
) -> ScenarioConstraintResults:
    """Check all constraints for a scenario.

    Args:
        scenario: Scenario to check
        constraints: List of constraint definitions
        simulation_results: Optional simulation results for probabilistic checks

    Returns:
        ScenarioConstraintResults
    """
    results = []

    for constraint in constraints:
        # Try to get metric from simulation results first
        if simulation_results is not None:
            values = get_metric_from_simulation(simulation_results, constraint.metric)
            if values is not None:
                result = check_constraint_probabilistic(constraint, values)
                results.append(result)
                continue

        # Fall back to deterministic check from scenario
        value = get_metric_value(scenario, constraint.metric)
        if value is not None:
            result = check_constraint_deterministic(constraint, value)
            results.append(result)
        else:
            # Unknown metric
            results.append(ConstraintResult(
                constraint_id=constraint.id,
                constraint_name=constraint.name,
                status=ConstraintStatus.UNKNOWN,
                actual_value=0.0,
                threshold_value=constraint.threshold,
                probability_met=0.0,
                message=f"Could not find metric '{constraint.metric}'",
            ))

    # Compute summary
    hard_constraints = [
        r for r, c in zip(results, constraints)
        if c.constraint_type == "hard"
    ]
    all_hard_pass = all(
        r.status in (ConstraintStatus.PASS, ConstraintStatus.WARNING)
        for r in hard_constraints
    )

    passed = sum(1 for r in results if r.status == ConstraintStatus.PASS)
    warnings = sum(1 for r in results if r.status == ConstraintStatus.WARNING)
    failed = sum(1 for r in results if r.status == ConstraintStatus.FAIL)

    return ScenarioConstraintResults(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        results=results,
        all_hard_constraints_pass=all_hard_pass,
        total_constraints=len(results),
        passed_constraints=passed,
        warning_constraints=warnings,
        failed_constraints=failed,
    )


def filter_feasible_scenarios(
    scenarios: ComposedScenarioSet,
    constraints: List[ConstraintDefinition],
    simulation_results_map: Optional[Dict[str, SimulationResults]] = None,
) -> List[ComposedScenario]:
    """Filter scenarios to only those satisfying all hard constraints.

    Args:
        scenarios: Set of scenarios
        constraints: Constraint definitions
        simulation_results_map: Optional map of scenario_id -> SimulationResults

    Returns:
        List of feasible scenarios
    """
    feasible = []

    for scenario_id, scenario in scenarios.scenarios.items():
        sim_results = None
        if simulation_results_map:
            sim_results = simulation_results_map.get(scenario_id)

        check_results = check_scenario_constraints(scenario, constraints, sim_results)
        if check_results.all_hard_constraints_pass:
            feasible.append(scenario)

    return feasible


# Default constraint definitions for Hallar
DEFAULT_HALLAR_CONSTRAINTS = [
    ConstraintDefinition(
        id="C1",
        name="Minimum Affordability",
        name_is="Lágmarks hagkvæmni",
        description="At least 25% of units must be affordable",
        constraint_type="hard",
        category="affordability",
        metric="affordability_percentage",
        operator=">=",
        threshold=0.25,
    ),
    ConstraintDefinition(
        id="C2",
        name="Maximum Default Risk",
        name_is="Hámarks vanskilaáhætta",
        description="Counterparty default probability must be under 15%",
        constraint_type="hard",
        category="financial",
        metric="default_probability",
        operator="<=",
        threshold=0.15,
    ),
    ConstraintDefinition(
        id="C3",
        name="First Units Timeline",
        name_is="Fyrstu einingar",
        description="First units must be delivered within 36 months",
        constraint_type="soft",
        category="timeline",
        metric="first_units_months",
        operator="<=",
        threshold=36,
        probability_threshold=0.80,
    ),
    ConstraintDefinition(
        id="C4",
        name="Positive Expected NPV",
        name_is="Jákvætt vænt NPV",
        description="Expected NPV must be positive",
        constraint_type="soft",
        category="financial",
        metric="npv",
        operator=">=",
        threshold=0,
        probability_threshold=0.70,
    ),
]
