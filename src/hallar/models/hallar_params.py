"""Hallar site-specific parameters for the DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from hallar.models.scenario import PERTParams


@dataclass
class SiteInfo:
    """Basic site information."""

    name: str
    location: str
    total_area_hectares: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SiteInfo":
        """Create SiteInfo from a dictionary."""
        return cls(
            name=data["name"],
            location=data["location"],
            total_area_hectares=data["total_area_hectares"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "location": self.location,
            "total_area_hectares": self.total_area_hectares,
        }


@dataclass
class BuildableArea:
    """Buildable area breakdown."""

    total_sqm: int
    residential_sqm: int
    commercial_sqm: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BuildableArea":
        """Create BuildableArea from a dictionary."""
        return cls(
            total_sqm=data["total_sqm"],
            residential_sqm=data["residential_sqm"],
            commercial_sqm=data["commercial_sqm"],
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "total_sqm": self.total_sqm,
            "residential_sqm": self.residential_sqm,
            "commercial_sqm": self.commercial_sqm,
        }


@dataclass
class UnitAssumptions:
    """Unit count assumptions."""

    average_unit_size_sqm: int
    total_units: int
    units_per_phase: int
    number_of_phases: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnitAssumptions":
        """Create UnitAssumptions from a dictionary."""
        return cls(
            average_unit_size_sqm=data["average_unit_size_sqm"],
            total_units=data["total_units"],
            units_per_phase=data["units_per_phase"],
            number_of_phases=data["number_of_phases"],
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "average_unit_size_sqm": self.average_unit_size_sqm,
            "total_units": self.total_units,
            "units_per_phase": self.units_per_phase,
            "number_of_phases": self.number_of_phases,
        }


@dataclass
class ByggingarretturValuation:
    """Valuation of development rights."""

    per_sqm: PERTParams
    total_value: PERTParams
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ByggingarretturValuation":
        """Create ByggingarretturValuation from a dictionary."""
        return cls(
            per_sqm=PERTParams.from_dict(data["per_sqm"]),
            total_value=PERTParams.from_dict(data["total_value"]),
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "per_sqm": self.per_sqm.to_dict(),
            "total_value": self.total_value.to_dict(),
            "notes": self.notes,
        }


@dataclass
class InfrastructureCostItem:
    """Cost breakdown for an infrastructure category."""

    share: float
    cost: PERTParams
    includes: List[str]
    capacity: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InfrastructureCostItem":
        """Create InfrastructureCostItem from a dictionary."""
        return cls(
            share=data["share"],
            cost=PERTParams.from_dict(data["cost"]),
            includes=data.get("includes", []),
            capacity=data.get("capacity"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "share": self.share,
            "cost": self.cost.to_dict(),
            "includes": self.includes,
        }
        if self.capacity is not None:
            result["capacity"] = self.capacity
        return result


@dataclass
class InfrastructureCosts:
    """Infrastructure cost breakdown."""

    total: PERTParams
    breakdown: Dict[str, InfrastructureCostItem]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InfrastructureCosts":
        """Create InfrastructureCosts from a dictionary."""
        breakdown = {}
        for cat_name, cat_data in data.get("breakdown", {}).items():
            breakdown[cat_name] = InfrastructureCostItem.from_dict(cat_data)
        return cls(
            total=PERTParams.from_dict(data["total"]),
            breakdown=breakdown,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total": self.total.to_dict(),
            "breakdown": {k: v.to_dict() for k, v in self.breakdown.items()},
        }


@dataclass
class ConstructionCosts:
    """Construction cost parameters."""

    residential: PERTParams
    affordable_residential: PERTParams
    commercial: PERTParams
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConstructionCosts":
        """Create ConstructionCosts from a dictionary."""
        return cls(
            residential=PERTParams.from_dict(data["residential"]),
            affordable_residential=PERTParams.from_dict(data["affordable_residential"]),
            commercial=PERTParams.from_dict(data["commercial"]),
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "residential": self.residential.to_dict(),
            "affordable_residential": self.affordable_residential.to_dict(),
            "commercial": self.commercial.to_dict(),
            "notes": self.notes,
        }


@dataclass
class RevenueAssumptions:
    """Revenue/price assumptions."""

    market_residential: PERTParams
    affordable_residential: PERTParams
    commercial: PERTParams
    discount_from_market: float
    rental_yield_annual: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RevenueAssumptions":
        """Create RevenueAssumptions from a dictionary."""
        affordable_data = data.get("affordable_residential", {})
        return cls(
            market_residential=PERTParams.from_dict(data["market_residential"]),
            affordable_residential=PERTParams.from_dict({
                "min": affordable_data.get("min", data["market_residential"]["min"] * 0.75),
                "likely": affordable_data.get("likely", data["market_residential"]["likely"] * 0.75),
                "max": affordable_data.get("max", data["market_residential"]["max"] * 0.75),
            }),
            commercial=PERTParams.from_dict(data["commercial"]),
            discount_from_market=affordable_data.get("discount_from_market", 0.25),
            rental_yield_annual=data.get("rental_yield", {}).get("annual", 0.045),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "market_residential": self.market_residential.to_dict(),
            "affordable_residential": {
                **self.affordable_residential.to_dict(),
                "discount_from_market": self.discount_from_market,
            },
            "commercial": self.commercial.to_dict(),
            "rental_yield": {"annual": self.rental_yield_annual},
        }


@dataclass
class TimelineAssumptions:
    """Timeline assumptions for project milestones."""

    planning_and_permits: PERTParams
    first_units_complete: PERTParams
    school_complete: PERTParams
    sixty_percent_complete: PERTParams
    full_completion: PERTParams
    critical_milestones: Dict[str, int]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineAssumptions":
        """Create TimelineAssumptions from a dictionary."""
        return cls(
            planning_and_permits=PERTParams.from_dict(data["planning_and_permits"]),
            first_units_complete=PERTParams.from_dict(data["first_units_complete"]),
            school_complete=PERTParams.from_dict(data["school_complete"]),
            sixty_percent_complete=PERTParams.from_dict(data["sixty_percent_complete"]),
            full_completion=PERTParams.from_dict(data["full_completion"]),
            critical_milestones=data.get("critical_milestones", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "planning_and_permits": self.planning_and_permits.to_dict(),
            "first_units_complete": self.first_units_complete.to_dict(),
            "school_complete": self.school_complete.to_dict(),
            "sixty_percent_complete": self.sixty_percent_complete.to_dict(),
            "full_completion": self.full_completion.to_dict(),
            "critical_milestones": self.critical_milestones,
        }


@dataclass
class MarketContext:
    """Current market context parameters."""

    housing_shortage: bool
    annual_demand_reykjavik: int
    mortgage_rate: float
    construction_loan_rate: float
    pension_fund_lending_rate: float
    inflation_rate: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketContext":
        """Create MarketContext from a dictionary."""
        rates = data.get("current_interest_rates", {})
        return cls(
            housing_shortage=data.get("housing_shortage", True),
            annual_demand_reykjavik=data.get("annual_demand_reykjavik", 2500),
            mortgage_rate=rates.get("mortgage", 0.065),
            construction_loan_rate=rates.get("construction_loan", 0.08),
            pension_fund_lending_rate=rates.get("pension_fund_lending", 0.045),
            inflation_rate=data.get("inflation_rate", 0.06),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "housing_shortage": self.housing_shortage,
            "annual_demand_reykjavik": self.annual_demand_reykjavik,
            "current_interest_rates": {
                "mortgage": self.mortgage_rate,
                "construction_loan": self.construction_loan_rate,
                "pension_fund_lending": self.pension_fund_lending_rate,
            },
            "inflation_rate": self.inflation_rate,
        }


@dataclass
class DiscountRates:
    """Discount rates for NPV calculations."""

    city_real: float
    city_nominal: float
    developer_real: float
    developer_nominal: float
    pension_real: float
    pension_nominal: float

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscountRates":
        """Create DiscountRates from a dictionary."""
        city = data.get("city", {})
        developer = data.get("developer", {})
        pension = data.get("pension_fund", {})
        return cls(
            city_real=city.get("real", 0.03),
            city_nominal=city.get("nominal", 0.09),
            developer_real=developer.get("real", 0.10),
            developer_nominal=developer.get("nominal", 0.16),
            pension_real=pension.get("real", 0.035),
            pension_nominal=pension.get("nominal", 0.095),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "city": {"real": self.city_real, "nominal": self.city_nominal},
            "developer": {"real": self.developer_real, "nominal": self.developer_nominal},
            "pension_fund": {"real": self.pension_real, "nominal": self.pension_nominal},
        }


@dataclass
class PoliticalContext:
    """Political context for decision making."""

    election_cycle_years: int
    next_election: str
    current_coalition: str
    housing_policy_priority: str
    affordability_target: float
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PoliticalContext":
        """Create PoliticalContext from a dictionary."""
        return cls(
            election_cycle_years=data.get("election_cycle_years", 4),
            next_election=data.get("next_election", ""),
            current_coalition=data.get("current_coalition", ""),
            housing_policy_priority=data.get("housing_policy_priority", "medium"),
            affordability_target=data.get("affordability_target", 0.25),
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "election_cycle_years": self.election_cycle_years,
            "next_election": self.next_election,
            "current_coalition": self.current_coalition,
            "housing_policy_priority": self.housing_policy_priority,
            "affordability_target": self.affordability_target,
            "notes": self.notes,
        }


@dataclass
class HallarParameters:
    """Complete Hallar site parameters."""

    site: SiteInfo
    buildable_area: BuildableArea
    units: UnitAssumptions
    byggingarrettur_valuation: ByggingarretturValuation
    infrastructure_costs: InfrastructureCosts
    construction_costs: ConstructionCosts
    revenue: RevenueAssumptions
    timeline: TimelineAssumptions
    market_context: MarketContext
    discount_rates: DiscountRates
    political_context: PoliticalContext

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HallarParameters":
        """Create HallarParameters from a dictionary."""
        return cls(
            site=SiteInfo.from_dict(data["hallar_site"]),
            buildable_area=BuildableArea.from_dict(data["buildable_area"]),
            units=UnitAssumptions.from_dict(data["unit_assumptions"]),
            byggingarrettur_valuation=ByggingarretturValuation.from_dict(data["byggingarrettur_valuation"]),
            infrastructure_costs=InfrastructureCosts.from_dict(data["infrastructure_costs"]),
            construction_costs=ConstructionCosts.from_dict(data["construction_costs"]),
            revenue=RevenueAssumptions.from_dict(data["revenue_assumptions"]),
            timeline=TimelineAssumptions.from_dict(data["timeline_assumptions"]),
            market_context=MarketContext.from_dict(data["market_context"]),
            discount_rates=DiscountRates.from_dict(data["discount_rates"]),
            political_context=PoliticalContext.from_dict(data["political_context"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hallar_site": self.site.to_dict(),
            "buildable_area": self.buildable_area.to_dict(),
            "unit_assumptions": self.units.to_dict(),
            "byggingarrettur_valuation": self.byggingarrettur_valuation.to_dict(),
            "infrastructure_costs": self.infrastructure_costs.to_dict(),
            "construction_costs": self.construction_costs.to_dict(),
            "revenue_assumptions": self.revenue.to_dict(),
            "timeline_assumptions": self.timeline.to_dict(),
            "market_context": self.market_context.to_dict(),
            "discount_rates": self.discount_rates.to_dict(),
            "political_context": self.political_context.to_dict(),
        }
