"""Data models for Hallar DSS."""

from hallar.models.scenario import (
    Scenario,
    PERTParams,
    RiskParams,
    AffordabilityParams,
    QualityParams,
    JVParams,
    TimelineParams,
)
from hallar.models.market import MarketScenario, MarketParams
from hallar.models.constraints import Constraint, ConstraintSet, ConstraintType
from hallar.models.weights import WeightProfile

# New expanded models
from hallar.models.goals import Goal, GoalDirection, WeightPreset, GoalSet
from hallar.models.ownership import OwnershipStructure, OwnershipSet
from hallar.models.financing import FinancingModel, FinancingCost, FinancingSet
from hallar.models.byggingarrettur import (
    ByggingarretturOption,
    ByggingarretturPricing,
    CityReceives,
    ByggingarretturSet,
)
from hallar.models.infrastructure import (
    InfrastructureModel,
    InfrastructureCost,
    InfrastructureSet,
)
from hallar.models.counterparty import CounterpartyProfile, CounterpartySet
from hallar.models.risks import Risk, RiskImpact, RiskCatalog
from hallar.models.composed import (
    ComposedScenario,
    ComposedScenarioSet,
    ScenarioComponents,
    GoalScores,
    EquityStructure,
    AffordabilityCommitment,
    PhaseStructure,
)
from hallar.models.hallar_params import (
    HallarParameters,
    SiteInfo,
    BuildableArea,
    UnitAssumptions,
    ByggingarretturValuation,
    InfrastructureCosts,
    ConstructionCosts,
    RevenueAssumptions,
    TimelineAssumptions,
    MarketContext,
    DiscountRates,
    PoliticalContext,
)

__all__ = [
    # Original models
    "Scenario",
    "PERTParams",
    "RiskParams",
    "AffordabilityParams",
    "QualityParams",
    "JVParams",
    "TimelineParams",
    "MarketScenario",
    "MarketParams",
    "Constraint",
    "ConstraintSet",
    "ConstraintType",
    "WeightProfile",
    # Goals
    "Goal",
    "GoalDirection",
    "WeightPreset",
    "GoalSet",
    # Ownership
    "OwnershipStructure",
    "OwnershipSet",
    # Financing
    "FinancingModel",
    "FinancingCost",
    "FinancingSet",
    # Byggingarrétt
    "ByggingarretturOption",
    "ByggingarretturPricing",
    "CityReceives",
    "ByggingarretturSet",
    # Infrastructure
    "InfrastructureModel",
    "InfrastructureCost",
    "InfrastructureSet",
    # Counterparty
    "CounterpartyProfile",
    "CounterpartySet",
    # Risks
    "Risk",
    "RiskImpact",
    "RiskCatalog",
    # Composed scenarios
    "ComposedScenario",
    "ComposedScenarioSet",
    "ScenarioComponents",
    "GoalScores",
    "EquityStructure",
    "AffordabilityCommitment",
    "PhaseStructure",
    # Hallar parameters
    "HallarParameters",
    "SiteInfo",
    "BuildableArea",
    "UnitAssumptions",
    "ByggingarretturValuation",
    "InfrastructureCosts",
    "ConstructionCosts",
    "RevenueAssumptions",
    "TimelineAssumptions",
    "MarketContext",
    "DiscountRates",
    "PoliticalContext",
]
