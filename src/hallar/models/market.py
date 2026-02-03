"""Market scenario data models for Hallar DSS."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class MarketParams:
    """Economic parameters for a market scenario."""

    construction_cost_multiplier: float
    interest_rate: float
    property_price_growth: float  # Annual growth rate
    sales_velocity_months: int  # Months to sell completed units
    inflation_rate: float
    developer_default_multiplier: float = 1.0  # Multiplier for default probability

    def __post_init__(self) -> None:
        if self.construction_cost_multiplier <= 0:
            raise ValueError("construction_cost_multiplier must be positive")
        if self.interest_rate < 0:
            raise ValueError("interest_rate must be non-negative")
        if self.sales_velocity_months <= 0:
            raise ValueError("sales_velocity_months must be positive")
        if self.developer_default_multiplier < 0:
            raise ValueError("developer_default_multiplier must be non-negative")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketParams":
        """Create MarketParams from a dictionary."""
        return cls(
            construction_cost_multiplier=data["construction_cost_multiplier"],
            interest_rate=data["interest_rate"],
            property_price_growth=data["property_price_growth"],
            sales_velocity_months=data["sales_velocity_months"],
            inflation_rate=data["inflation_rate"],
            developer_default_multiplier=data.get("developer_default_multiplier", 1.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "construction_cost_multiplier": self.construction_cost_multiplier,
            "interest_rate": self.interest_rate,
            "property_price_growth": self.property_price_growth,
            "sales_velocity_months": self.sales_velocity_months,
            "inflation_rate": self.inflation_rate,
            "developer_default_multiplier": self.developer_default_multiplier,
        }


@dataclass
class MarketScenario:
    """Complete market scenario definition."""

    id: str
    name: str
    description: str
    probability: float  # Probability weight for expected value calculations
    parameters: MarketParams

    def __post_init__(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("probability must be between 0 and 1")

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "MarketScenario":
        """Create MarketScenario from a dictionary."""
        return cls(
            id=id,
            name=data["name"],
            description=data.get("description", ""),
            probability=data["probability"],
            parameters=MarketParams.from_dict(data["parameters"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "probability": self.probability,
            "parameters": self.parameters.to_dict(),
        }
