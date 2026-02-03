"""Scenario data models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class PERTParams:
    """PERT distribution parameters for uncertain values."""

    min: float
    likely: float
    max: float

    def validate(self) -> None:
        """Validate that min <= likely <= max."""
        if not (self.min <= self.likely <= self.max):
            raise ValueError(
                f"Invalid PERT parameters: min ({self.min}) <= likely ({self.likely}) <= max ({self.max}) required"
            )

    def __post_init__(self) -> None:
        self.validate()

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "PERTParams":
        """Create PERTParams from a dictionary."""
        return cls(
            min=data["min"],
            likely=data["likely"],
            max=data["max"],
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {"min": self.min, "likely": self.likely, "max": self.max}


@dataclass
class RiskParams:
    """Risk parameters for a scenario."""

    cost_overrun_probability: float
    cost_overrun_multiplier: PERTParams
    developer_default_probability: float
    delay_probability: float
    delay_months: PERTParams

    def __post_init__(self) -> None:
        # Validate probabilities are in [0, 1]
        for name, prob in [
            ("cost_overrun_probability", self.cost_overrun_probability),
            ("developer_default_probability", self.developer_default_probability),
            ("delay_probability", self.delay_probability),
        ]:
            if not 0 <= prob <= 1:
                raise ValueError(f"{name} must be between 0 and 1, got {prob}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskParams":
        """Create RiskParams from a dictionary."""
        return cls(
            cost_overrun_probability=data["cost_overrun_probability"],
            cost_overrun_multiplier=PERTParams.from_dict(data["cost_overrun_multiplier"]),
            developer_default_probability=data.get("developer_default_probability", 0.0),
            delay_probability=data["delay_probability"],
            delay_months=PERTParams.from_dict(data["delay_months"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "cost_overrun_probability": self.cost_overrun_probability,
            "cost_overrun_multiplier": self.cost_overrun_multiplier.to_dict(),
            "developer_default_probability": self.developer_default_probability,
            "delay_probability": self.delay_probability,
            "delay_months": self.delay_months.to_dict(),
        }


@dataclass
class AffordabilityParams:
    """Affordability commitment parameters."""

    percentage_affordable: float  # 0-1
    price_discount: float  # 0-1 (e.g., 0.2 = 20% below market)
    restriction_years: int
    legally_binding: bool
    rental_percentage: float = 0.0  # 0-1, fraction of units that are rental

    def __post_init__(self) -> None:
        if not 0 <= self.percentage_affordable <= 1:
            raise ValueError(f"percentage_affordable must be between 0 and 1")
        if not 0 <= self.price_discount <= 1:
            raise ValueError(f"price_discount must be between 0 and 1")
        if self.restriction_years < 0:
            raise ValueError(f"restriction_years must be non-negative")
        if not 0 <= self.rental_percentage <= 1:
            raise ValueError(f"rental_percentage must be between 0 and 1")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AffordabilityParams":
        """Create AffordabilityParams from a dictionary."""
        return cls(
            percentage_affordable=data["percentage_affordable"],
            price_discount=data["price_discount"],
            restriction_years=data["restriction_years"],
            legally_binding=data["legally_binding"],
            rental_percentage=data.get("rental_percentage", 0.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "percentage_affordable": self.percentage_affordable,
            "price_discount": self.price_discount,
            "restriction_years": self.restriction_years,
            "legally_binding": self.legally_binding,
            "rental_percentage": self.rental_percentage,
        }


@dataclass
class QualityParams:
    """Quality parameters for a scenario."""

    energy_rating: str  # A+, A, B, C, D
    defect_rate: PERTParams

    VALID_RATINGS = ["A+", "A", "B", "C", "D", "E", "F", "G"]

    def __post_init__(self) -> None:
        if self.energy_rating not in self.VALID_RATINGS:
            raise ValueError(f"energy_rating must be one of {self.VALID_RATINGS}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityParams":
        """Create QualityParams from a dictionary."""
        return cls(
            energy_rating=data["energy_rating"],
            defect_rate=PERTParams.from_dict(data["defect_rate"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "energy_rating": self.energy_rating,
            "defect_rate": self.defect_rate.to_dict(),
        }


@dataclass
class JVParams:
    """Joint Venture specific parameters."""

    city_equity_share: float  # 0-1
    profit_share: float  # 0-1
    loss_share: float  # 0-1
    management_fee_annual: float  # ISK millions

    def __post_init__(self) -> None:
        for name, val in [
            ("city_equity_share", self.city_equity_share),
            ("profit_share", self.profit_share),
            ("loss_share", self.loss_share),
        ]:
            if not 0 <= val <= 1:
                raise ValueError(f"{name} must be between 0 and 1")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JVParams":
        """Create JVParams from a dictionary."""
        return cls(
            city_equity_share=data["city_equity_share"],
            profit_share=data["profit_share"],
            loss_share=data["loss_share"],
            management_fee_annual=data["management_fee_annual"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "city_equity_share": self.city_equity_share,
            "profit_share": self.profit_share,
            "loss_share": self.loss_share,
            "management_fee_annual": self.management_fee_annual,
        }


@dataclass
class TimelineParams:
    """Timeline parameters for scenario milestones."""

    first_units: PERTParams
    first_school: PERTParams
    sixty_percent_complete: PERTParams

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineParams":
        """Create TimelineParams from a dictionary."""
        return cls(
            first_units=PERTParams.from_dict(data["first_units"]),
            first_school=PERTParams.from_dict(data["first_school"]),
            sixty_percent_complete=PERTParams.from_dict(data["sixty_percent_complete"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "first_units": self.first_units.to_dict(),
            "first_school": self.first_school.to_dict(),
            "sixty_percent_complete": self.sixty_percent_complete.to_dict(),
        }


@dataclass
class Scenario:
    """Complete scenario definition for land development."""

    id: str
    name: str
    description: str
    infrastructure_cost: PERTParams
    rights_revenue: PERTParams
    timeline: TimelineParams
    risks: RiskParams
    affordability: AffordabilityParams
    quality: QualityParams
    city_control: float  # 0-1
    step_in_cost_fraction: float  # 0-1
    jv_params: Optional[JVParams] = None

    def __post_init__(self) -> None:
        if not 0 <= self.city_control <= 1:
            raise ValueError("city_control must be between 0 and 1")
        if not 0 <= self.step_in_cost_fraction <= 1:
            raise ValueError("step_in_cost_fraction must be between 0 and 1")

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "Scenario":
        """Create Scenario from a dictionary."""
        jv_params = None
        if "jv_parameters" in data:
            jv_params = JVParams.from_dict(data["jv_parameters"])

        return cls(
            id=id,
            name=data["name"],
            description=data["description"],
            infrastructure_cost=PERTParams.from_dict(data["infrastructure_cost"]),
            rights_revenue=PERTParams.from_dict(data["rights_revenue"]),
            timeline=TimelineParams.from_dict(data["timeline"]),
            risks=RiskParams.from_dict(data["risks"]),
            affordability=AffordabilityParams.from_dict(data["affordability"]),
            quality=QualityParams.from_dict(data["quality"]),
            city_control=data.get("city_control", 0.5),
            step_in_cost_fraction=data.get("step_in_cost_fraction", 0.0),
            jv_params=jv_params,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "description": self.description,
            "infrastructure_cost": self.infrastructure_cost.to_dict(),
            "rights_revenue": self.rights_revenue.to_dict(),
            "timeline": self.timeline.to_dict(),
            "risks": self.risks.to_dict(),
            "affordability": self.affordability.to_dict(),
            "quality": self.quality.to_dict(),
            "city_control": self.city_control,
            "step_in_cost_fraction": self.step_in_cost_fraction,
        }
        if self.jv_params:
            result["jv_parameters"] = self.jv_params.to_dict()
        return result
