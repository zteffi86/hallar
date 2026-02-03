"""Structure composer for building and validating scenario combinations."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from itertools import product

from hallar.models import (
    OwnershipStructure,
    OwnershipSet,
    FinancingModel,
    FinancingSet,
    ByggingarretturOption,
    ByggingarretturSet,
    InfrastructureModel,
    InfrastructureSet,
    CounterpartyProfile,
    CounterpartySet,
    ComposedScenario,
    ScenarioComponents,
    GoalScores,
)


@dataclass
class CompatibilityIssue:
    """An incompatibility between components."""

    component_a: str
    component_b: str
    reason: str
    severity: str  # "error", "warning"


@dataclass
class CompositionValidation:
    """Result of validating a scenario composition."""

    is_valid: bool
    issues: List[CompatibilityIssue]
    warnings: List[str]
    component_ids: Dict[str, str]


def check_ownership_financing_compatibility(
    ownership: OwnershipStructure,
    financing: FinancingModel,
) -> Optional[CompatibilityIssue]:
    """Check if ownership and financing models are compatible.

    Args:
        ownership: Ownership structure
        financing: Financing model

    Returns:
        CompatibilityIssue if incompatible, None otherwise
    """
    # Check if financing is in ownership's compatible list
    if ownership.compatible_financing and financing.id not in ownership.compatible_financing:
        return CompatibilityIssue(
            component_a=f"Ownership:{ownership.id}",
            component_b=f"Financing:{financing.id}",
            reason=f"{ownership.name} is not compatible with {financing.name}",
            severity="error",
        )

    # Check if ownership is in financing's compatible list
    if financing.compatible_ownership and ownership.id not in financing.compatible_ownership:
        return CompatibilityIssue(
            component_a=f"Financing:{financing.id}",
            component_b=f"Ownership:{ownership.id}",
            reason=f"{financing.name} is not compatible with {ownership.name}",
            severity="error",
        )

    return None


def check_ownership_byggingarrettur_compatibility(
    ownership: OwnershipStructure,
    byggingarrettur: ByggingarretturOption,
) -> Optional[CompatibilityIssue]:
    """Check if ownership and byggingarrétt options are compatible.

    Args:
        ownership: Ownership structure
        byggingarrettur: Byggingarrétt option

    Returns:
        CompatibilityIssue if incompatible, None otherwise
    """
    # Check if ownership is in byggingarrétt's compatible list
    compatible_ownership = byggingarrettur.compatible_with.get("ownership", [])
    if compatible_ownership and ownership.id not in compatible_ownership:
        return CompatibilityIssue(
            component_a=f"Byggingarrétt:{byggingarrettur.id}",
            component_b=f"Ownership:{ownership.id}",
            reason=f"{byggingarrettur.name} is not compatible with {ownership.name}",
            severity="error",
        )

    # Check if byggingarrétt is in ownership's compatible list
    if ownership.compatible_byggingarrettur and byggingarrettur.id not in ownership.compatible_byggingarrettur:
        return CompatibilityIssue(
            component_a=f"Ownership:{ownership.id}",
            component_b=f"Byggingarrétt:{byggingarrettur.id}",
            reason=f"{ownership.name} is not compatible with {byggingarrettur.name}",
            severity="error",
        )

    return None


def check_financing_byggingarrettur_compatibility(
    financing: FinancingModel,
    byggingarrettur: ByggingarretturOption,
) -> Optional[CompatibilityIssue]:
    """Check if financing and byggingarrétt options are compatible.

    Args:
        financing: Financing model
        byggingarrettur: Byggingarrétt option

    Returns:
        CompatibilityIssue if incompatible, None otherwise
    """
    compatible_financing = byggingarrettur.compatible_with.get("financing", [])
    if compatible_financing and financing.id not in compatible_financing:
        return CompatibilityIssue(
            component_a=f"Byggingarrétt:{byggingarrettur.id}",
            component_b=f"Financing:{financing.id}",
            reason=f"{byggingarrettur.name} is not compatible with {financing.name}",
            severity="error",
        )
    return None


def validate_composition(
    ownership: OwnershipStructure,
    financing: FinancingModel,
    byggingarrettur: Optional[ByggingarretturOption],
    infrastructure: InfrastructureModel,
) -> CompositionValidation:
    """Validate a complete scenario composition.

    Args:
        ownership: Ownership structure
        financing: Financing model
        byggingarrettur: Byggingarrétt option (optional for city-only)
        infrastructure: Infrastructure model

    Returns:
        CompositionValidation result
    """
    issues = []
    warnings = []

    # Check ownership-financing compatibility
    issue = check_ownership_financing_compatibility(ownership, financing)
    if issue:
        issues.append(issue)

    # Check ownership-byggingarrétt compatibility (if applicable)
    if byggingarrettur:
        issue = check_ownership_byggingarrettur_compatibility(ownership, byggingarrettur)
        if issue:
            issues.append(issue)

        issue = check_financing_byggingarrettur_compatibility(financing, byggingarrettur)
        if issue:
            issues.append(issue)

    # Check infrastructure compatibility
    if infrastructure.compatible_ownership:
        if ownership.id not in infrastructure.compatible_ownership:
            issues.append(CompatibilityIssue(
                component_a=f"Infrastructure:{infrastructure.id}",
                component_b=f"Ownership:{ownership.id}",
                reason=f"{infrastructure.name} is not compatible with {ownership.name}",
                severity="error",
            ))

    # Add warnings for potential issues
    if financing.city_cash_requirement == "high" and ownership.city_control < 50:
        warnings.append(
            f"High city cash requirement with low city control ({ownership.city_control}%)"
        )

    component_ids = {
        "ownership": ownership.id,
        "financing": financing.id,
        "byggingarrettur": byggingarrettur.id if byggingarrettur else "N/A",
        "infrastructure": infrastructure.id,
    }

    return CompositionValidation(
        is_valid=len([i for i in issues if i.severity == "error"]) == 0,
        issues=issues,
        warnings=warnings,
        component_ids=component_ids,
    )


def estimate_goal_scores(
    ownership: OwnershipStructure,
    financing: FinancingModel,
    byggingarrettur: Optional[ByggingarretturOption],
    infrastructure: InfrastructureModel,
    counterparty: Optional[CounterpartyProfile],
) -> GoalScores:
    """Estimate goal scores for a composed scenario.

    Args:
        ownership: Ownership structure
        financing: Financing model
        byggingarrettur: Byggingarrétt option
        infrastructure: Infrastructure model
        counterparty: Counterparty profile

    Returns:
        Estimated GoalScores
    """
    # Speed: Based on financing availability and infrastructure timing
    speed = 50
    if financing.city_cash_requirement == "low":
        speed += 15
    elif financing.city_cash_requirement == "high":
        speed -= 15
    if infrastructure.timing == "parallel":
        speed += 10
    elif infrastructure.timing == "before_construction":
        speed -= 10

    # Affordability: Based on ownership control and byggingarrétt type
    affordability = 50
    if ownership.city_control >= 75:
        affordability += 30
    elif ownership.city_control >= 50:
        affordability += 15
    if byggingarrettur and byggingarrettur.pricing.method == "discounted":
        affordability += 20

    # Quality: Based on infrastructure quality control
    quality = 50
    if infrastructure.quality_control == "city":
        quality += 20
    elif infrastructure.quality_control == "joint":
        quality += 10
    if ownership.city_control >= 50:
        quality += 10

    # Financial: Based on financing cost and byggingarrétt pricing
    financial = 50
    if financing.cost.interest_rate < 0.05:
        financial += 15
    elif financing.cost.interest_rate > 0.08:
        financial -= 15
    if byggingarrettur and byggingarrettur.pricing.method == "market":
        financial += 20

    # Risk: Based on counterparty profile and financing structure
    risk = 50
    if counterparty:
        if counterparty.default_probability.likely < 0.02:
            risk += 30
        elif counterparty.default_probability.likely < 0.05:
            risk += 15
        elif counterparty.default_probability.likely > 0.10:
            risk -= 20
    if financing.city_cash_requirement == "low":
        risk += 10

    # Control: Directly from ownership
    control = ownership.city_control

    # Clamp all scores to 0-100
    return GoalScores(
        speed=max(0, min(100, speed)),
        affordability=max(0, min(100, affordability)),
        quality=max(0, min(100, quality)),
        financial=max(0, min(100, financial)),
        risk=max(0, min(100, risk)),
        control=max(0, min(100, control)),
    )


def compose_scenario(
    ownership: OwnershipStructure,
    financing: FinancingModel,
    byggingarrettur: Optional[ByggingarretturOption],
    infrastructure: InfrastructureModel,
    counterparty: Optional[CounterpartyProfile] = None,
    scenario_id: Optional[str] = None,
) -> Tuple[Optional[ComposedScenario], CompositionValidation]:
    """Compose a scenario from components.

    Args:
        ownership: Ownership structure
        financing: Financing model
        byggingarrettur: Byggingarrétt option
        infrastructure: Infrastructure model
        counterparty: Counterparty profile
        scenario_id: Optional ID for the scenario

    Returns:
        Tuple of (ComposedScenario or None, CompositionValidation)
    """
    validation = validate_composition(ownership, financing, byggingarrettur, infrastructure)

    if not validation.is_valid:
        return None, validation

    # Generate scenario ID if not provided
    if scenario_id is None:
        scenario_id = f"C_{ownership.id}_{financing.id}_{byggingarrettur.id if byggingarrettur else 'NA'}_{infrastructure.id}"

    # Estimate goal scores
    goal_scores = estimate_goal_scores(
        ownership, financing, byggingarrettur, infrastructure, counterparty
    )

    # Determine counterparty type
    counterparty_type = ownership.counterparty
    if counterparty:
        counterparty_type = counterparty.id

    # Get default probability
    default_prob = 0.05
    if counterparty:
        default_prob = counterparty.default_probability.likely

    components = ScenarioComponents(
        ownership=ownership.id,
        financing=financing.id,
        byggingarrettur=byggingarrettur.id if byggingarrettur else "N/A",
        infrastructure=infrastructure.id,
    )

    scenario = ComposedScenario(
        id=scenario_id,
        name=f"{ownership.name} + {financing.name}",
        name_is=f"{ownership.name_is} + {financing.name_is}",
        description=f"Composed scenario: {ownership.description}",
        components=components,
        counterparty=counterparty_type,
        default_probability=default_prob,
        city_control_score=ownership.city_control,
        goal_scores=goal_scores,
    )

    return scenario, validation


def generate_all_valid_combinations(
    ownership_set: OwnershipSet,
    financing_set: FinancingSet,
    byggingarrettur_set: ByggingarretturSet,
    infrastructure_set: InfrastructureSet,
    counterparty_set: Optional[CounterpartySet] = None,
) -> List[Tuple[ComposedScenario, CompositionValidation]]:
    """Generate all valid scenario combinations.

    Args:
        ownership_set: All ownership structures
        financing_set: All financing models
        byggingarrettur_set: All byggingarrétt options
        infrastructure_set: All infrastructure models
        counterparty_set: Counterparty profiles

    Returns:
        List of (ComposedScenario, CompositionValidation) tuples for valid combinations
    """
    valid_scenarios = []

    for ownership in ownership_set.structures.values():
        for financing in financing_set.models.values():
            # For city-only scenarios, byggingarrétt may not apply
            byggingarrettur_options = list(byggingarrettur_set.options.values())
            if ownership.id == "O1":  # City direct
                byggingarrettur_options = [None]

            for byggingarrettur in byggingarrettur_options:
                for infrastructure in infrastructure_set.models.values():
                    # Get counterparty profile
                    counterparty = None
                    if counterparty_set and ownership.counterparty:
                        counterparty = counterparty_set.get(ownership.counterparty)

                    scenario, validation = compose_scenario(
                        ownership, financing, byggingarrettur, infrastructure, counterparty
                    )

                    if scenario is not None:
                        valid_scenarios.append((scenario, validation))

    return valid_scenarios


def find_scenarios_matching_criteria(
    scenarios: List[ComposedScenario],
    min_affordability: Optional[int] = None,
    min_control: Optional[int] = None,
    max_risk: Optional[float] = None,
    counterparty_types: Optional[List[str]] = None,
) -> List[ComposedScenario]:
    """Filter scenarios by criteria.

    Args:
        scenarios: List of scenarios
        min_affordability: Minimum affordability score
        min_control: Minimum control score
        max_risk: Maximum default probability
        counterparty_types: Allowed counterparty types

    Returns:
        Filtered list of scenarios
    """
    filtered = scenarios

    if min_affordability is not None:
        filtered = [s for s in filtered if s.goal_scores.affordability >= min_affordability]

    if min_control is not None:
        filtered = [s for s in filtered if s.city_control_score >= min_control]

    if max_risk is not None:
        filtered = [s for s in filtered if s.get_default_probability_likely() <= max_risk]

    if counterparty_types is not None:
        filtered = [s for s in filtered if s.counterparty in counterparty_types]

    return filtered
