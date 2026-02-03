"""Risk analysis module for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np

from hallar.models import (
    ComposedScenario,
    ComposedScenarioSet,
    RiskCatalog,
    Risk,
    CounterpartySet,
    CounterpartyProfile,
    PERTParams,
)
from hallar.simulation.distributions import pert_distribution


@dataclass
class RiskAssessment:
    """Assessment of a single risk for a scenario."""

    risk_id: str
    risk_name: str
    probability: float  # Expected probability
    expected_impact: float  # Expected NPV impact in M ISK
    expected_loss: float  # probability * impact
    severity: str  # "low", "medium", "high", "critical"


@dataclass
class CounterpartyRiskAssessment:
    """Counterparty-specific risk assessment."""

    counterparty_type: str
    default_probability: float
    recovery_rate: float
    expected_loss_given_default: float  # (1 - recovery) * exposure
    financial_strength: str
    risk_factors: List[str]


@dataclass
class ScenarioRiskProfile:
    """Complete risk profile for a scenario."""

    scenario_id: str
    scenario_name: str
    counterparty_risk: CounterpartyRiskAssessment
    risk_assessments: List[RiskAssessment]
    total_expected_loss: float
    risk_score: float  # 0-100, lower is better
    risk_category: str  # "low", "moderate", "elevated", "high"


def assess_counterparty_risk(
    scenario: ComposedScenario,
    counterparties: CounterpartySet,
    exposure: float = 16500.0,  # Default: full byggingarrétt value in M ISK
) -> CounterpartyRiskAssessment:
    """Assess counterparty risk for a scenario.

    Args:
        scenario: Composed scenario
        counterparties: Counterparty profile set
        exposure: City's exposure in M ISK

    Returns:
        CounterpartyRiskAssessment
    """
    counterparty_type = scenario.counterparty
    profile = counterparties.get(counterparty_type)

    if profile is None:
        # Default for unknown counterparty
        return CounterpartyRiskAssessment(
            counterparty_type=counterparty_type,
            default_probability=0.05,
            recovery_rate=0.5,
            expected_loss_given_default=exposure * 0.5 * 0.05,
            financial_strength="unknown",
            risk_factors=["Unknown counterparty type"],
        )

    default_prob = profile.default_probability.likely
    lgd = (1 - profile.recovery_rate) * exposure
    expected_loss = lgd * default_prob

    return CounterpartyRiskAssessment(
        counterparty_type=counterparty_type,
        default_probability=default_prob,
        recovery_rate=profile.recovery_rate,
        expected_loss_given_default=expected_loss,
        financial_strength=profile.financial_strength,
        risk_factors=profile.risk_factors,
    )


def assess_risk(
    risk: Risk,
    scenario: ComposedScenario,
    base_npv: float = 5000.0,  # Default base NPV in M ISK
) -> RiskAssessment:
    """Assess a single risk for a scenario.

    Args:
        risk: Risk to assess
        scenario: Scenario being analyzed
        base_npv: Base NPV for impact calculations

    Returns:
        RiskAssessment
    """
    # Check if this risk affects this scenario
    if risk.affected_scenarios and scenario.id not in risk.affected_scenarios:
        return RiskAssessment(
            risk_id=risk.id,
            risk_name=risk.name,
            probability=0.0,
            expected_impact=0.0,
            expected_loss=0.0,
            severity="none",
        )

    probability = risk.probability.likely

    # Calculate expected impact
    impact = 0.0
    if risk.impact.npv_impact is not None:
        impact = risk.impact.npv_impact.likely
    elif risk.impact.cost_increase_pct is not None:
        # Assume cost is ~50% of base NPV, so cost increase reduces NPV
        cost_increase = risk.impact.cost_increase_pct.likely
        impact = -base_npv * 0.5 * cost_increase
    elif risk.impact.revenue_decrease_pct is not None:
        # Revenue decrease reduces NPV
        rev_decrease = risk.impact.revenue_decrease_pct.likely
        impact = -base_npv * rev_decrease

    expected_loss = probability * abs(impact)

    # Determine severity
    if expected_loss < 100:
        severity = "low"
    elif expected_loss < 500:
        severity = "medium"
    elif expected_loss < 1000:
        severity = "high"
    else:
        severity = "critical"

    return RiskAssessment(
        risk_id=risk.id,
        risk_name=risk.name,
        probability=probability,
        expected_impact=impact,
        expected_loss=expected_loss,
        severity=severity,
    )


def analyze_scenario_risks(
    scenario: ComposedScenario,
    risk_catalog: RiskCatalog,
    counterparties: CounterpartySet,
    base_npv: float = 5000.0,
    exposure: float = 16500.0,
) -> ScenarioRiskProfile:
    """Analyze all risks for a scenario.

    Args:
        scenario: Scenario to analyze
        risk_catalog: Catalog of risks
        counterparties: Counterparty profiles
        base_npv: Base NPV for calculations
        exposure: City's exposure

    Returns:
        ScenarioRiskProfile
    """
    # Assess counterparty risk
    counterparty_risk = assess_counterparty_risk(scenario, counterparties, exposure)

    # Assess all risks
    risk_assessments = []
    for risk in risk_catalog.risks.values():
        assessment = assess_risk(risk, scenario, base_npv)
        if assessment.expected_loss > 0:
            risk_assessments.append(assessment)

    # Sort by expected loss descending
    risk_assessments.sort(key=lambda r: r.expected_loss, reverse=True)

    # Calculate total expected loss
    total_expected_loss = (
        counterparty_risk.expected_loss_given_default +
        sum(r.expected_loss for r in risk_assessments)
    )

    # Calculate risk score (0-100, lower is better)
    # Based on total expected loss as percentage of exposure
    risk_ratio = total_expected_loss / exposure
    risk_score = min(100, risk_ratio * 1000)  # 10% loss = 100 score

    # Determine risk category
    if risk_score < 20:
        risk_category = "low"
    elif risk_score < 40:
        risk_category = "moderate"
    elif risk_score < 60:
        risk_category = "elevated"
    else:
        risk_category = "high"

    return ScenarioRiskProfile(
        scenario_id=scenario.id,
        scenario_name=scenario.name,
        counterparty_risk=counterparty_risk,
        risk_assessments=risk_assessments,
        total_expected_loss=total_expected_loss,
        risk_score=risk_score,
        risk_category=risk_category,
    )


def compare_scenario_risks(
    scenarios: ComposedScenarioSet,
    risk_catalog: RiskCatalog,
    counterparties: CounterpartySet,
) -> List[ScenarioRiskProfile]:
    """Compare risks across all scenarios.

    Args:
        scenarios: Set of scenarios
        risk_catalog: Catalog of risks
        counterparties: Counterparty profiles

    Returns:
        List of risk profiles sorted by risk score (lowest first)
    """
    profiles = []
    for scenario in scenarios.scenarios.values():
        profile = analyze_scenario_risks(
            scenario, risk_catalog, counterparties
        )
        profiles.append(profile)

    profiles.sort(key=lambda p: p.risk_score)
    return profiles


def simulate_risk_scenarios(
    scenario: ComposedScenario,
    risk_catalog: RiskCatalog,
    counterparties: CounterpartySet,
    n_simulations: int = 10000,
    base_npv: float = 5000.0,
    seed: Optional[int] = None,
) -> Dict[str, np.ndarray]:
    """Run Monte Carlo simulation of risk impacts.

    Args:
        scenario: Scenario to simulate
        risk_catalog: Catalog of risks
        counterparties: Counterparty profiles
        n_simulations: Number of simulations
        base_npv: Base NPV
        seed: Random seed

    Returns:
        Dictionary with arrays: 'npv_impacts', 'total_loss', 'risk_occurred'
    """
    rng = np.random.default_rng(seed)

    npv_impacts = np.zeros(n_simulations)
    counterparty_losses = np.zeros(n_simulations)
    risk_occurred = {}

    # Simulate counterparty default
    profile = counterparties.get(scenario.counterparty)
    if profile:
        default_probs = pert_distribution(
            profile.default_probability.min,
            profile.default_probability.likely,
            profile.default_probability.max,
            n_simulations,
            rng,
        )
        defaults = rng.random(n_simulations) < default_probs
        lgd = (1 - profile.recovery_rate) * base_npv
        counterparty_losses = np.where(defaults, lgd, 0)
        npv_impacts -= counterparty_losses

    # Simulate each risk
    for risk in risk_catalog.risks.values():
        if risk.affected_scenarios and scenario.id not in risk.affected_scenarios:
            continue

        # Sample probability and determine if risk occurs
        probs = pert_distribution(
            risk.probability.min,
            risk.probability.likely,
            risk.probability.max,
            n_simulations,
            rng,
        )
        occurred = rng.random(n_simulations) < probs
        risk_occurred[risk.id] = occurred

        # Calculate impact when risk occurs
        if risk.impact.npv_impact is not None:
            impacts = pert_distribution(
                risk.impact.npv_impact.min,
                risk.impact.npv_impact.likely,
                risk.impact.npv_impact.max,
                n_simulations,
                rng,
            )
            npv_impacts += np.where(occurred, impacts, 0)
        elif risk.impact.cost_increase_pct is not None:
            pct_increase = pert_distribution(
                risk.impact.cost_increase_pct.min,
                risk.impact.cost_increase_pct.likely,
                risk.impact.cost_increase_pct.max,
                n_simulations,
                rng,
            )
            npv_impacts -= np.where(occurred, base_npv * 0.5 * pct_increase, 0)

    return {
        "npv_impacts": npv_impacts,
        "counterparty_losses": counterparty_losses,
        "total_loss": -npv_impacts,  # Positive = loss
        "risk_occurred": risk_occurred,
    }


def calculate_var_cvar(
    losses: np.ndarray,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """Calculate Value at Risk and Conditional VaR.

    Args:
        losses: Array of losses (positive = loss)
        confidence: Confidence level (default 95%)

    Returns:
        Tuple of (VaR, CVaR) at confidence level
    """
    var = np.percentile(losses, confidence * 100)
    cvar = np.mean(losses[losses >= var])
    return var, cvar
