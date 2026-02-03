"""Financing model definitions for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class FinancingCost:
    """Cost parameters for a financing source."""

    interest_rate: float
    term_years: Optional[int] = None
    arrangement_fee: float = 0.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancingCost":
        """Create FinancingCost from a dictionary."""
        return cls(
            interest_rate=data.get("interest_rate", 0.0),
            term_years=data.get("term_years"),
            arrangement_fee=data.get("arrangement_fee", 0.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"interest_rate": self.interest_rate}
        if self.term_years is not None:
            result["term_years"] = self.term_years
        if self.arrangement_fee > 0:
            result["arrangement_fee"] = self.arrangement_fee
        return result


@dataclass
class FinancingModel:
    """A financing model for land development."""

    id: str
    name: str
    name_is: str
    description: str
    sources: List[str]  # e.g., ["city_budget", "bank_loan", "pension_fund"]
    cost: FinancingCost
    city_cash_requirement: str  # "high", "medium", "low", "none"
    leverage_ratio: Optional[float] = None
    compatible_ownership: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "FinancingModel":
        """Create FinancingModel from a dictionary."""
        cost_data = data.get("cost", {})
        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            sources=data.get("sources", []),
            cost=FinancingCost.from_dict(cost_data),
            city_cash_requirement=data.get("city_cash_requirement", "medium"),
            leverage_ratio=data.get("leverage_ratio"),
            compatible_ownership=data.get("compatible_ownership", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "sources": self.sources,
            "cost": self.cost.to_dict(),
            "city_cash_requirement": self.city_cash_requirement,
            "compatible_ownership": self.compatible_ownership,
        }
        if self.leverage_ratio is not None:
            result["leverage_ratio"] = self.leverage_ratio
        return result


@dataclass
class FinancingSet:
    """Collection of financing models."""

    models: Dict[str, FinancingModel]

    def get(self, model_id: str) -> Optional[FinancingModel]:
        """Get a financing model by ID."""
        return self.models.get(model_id)

    def get_by_cash_requirement(self, requirement: str) -> List[FinancingModel]:
        """Get financing models by city cash requirement level."""
        return [
            m for m in self.models.values()
            if m.city_cash_requirement == requirement
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancingSet":
        """Create FinancingSet from a dictionary."""
        models = {}
        financing_data = data.get("financing_models", data)
        for model_id, model_data in financing_data.items():
            if isinstance(model_data, dict):
                models[model_id] = FinancingModel.from_dict(model_id, model_data)
        return cls(models=models)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "financing_models": {
                mid: m.to_dict() for mid, m in self.models.items()
            }
        }
