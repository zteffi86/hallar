"""Infrastructure delivery models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from hallar.models.scenario import PERTParams


@dataclass
class InfrastructureCost:
    """Cost parameters for infrastructure delivery."""

    city_share: float  # 0-1, fraction of cost borne by city
    developer_share: float  # 0-1, fraction borne by developer
    other_share: float = 0.0  # 0-1, fraction from other sources

    def __post_init__(self) -> None:
        total = self.city_share + self.developer_share + self.other_share
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Cost shares must sum to 1, got {total}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InfrastructureCost":
        """Create InfrastructureCost from a dictionary."""
        return cls(
            city_share=data.get("city_share", 0.5),
            developer_share=data.get("developer_share", 0.5),
            other_share=data.get("other_share", 0.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "city_share": self.city_share,
            "developer_share": self.developer_share,
            "other_share": self.other_share,
        }


@dataclass
class InfrastructureModel:
    """An infrastructure delivery model."""

    id: str
    name: str
    name_is: str
    description: str
    delivery_by: str  # "city", "developer", "joint", "utility_company"
    cost_allocation: InfrastructureCost
    timing: str  # "before_construction", "parallel", "developer_led"
    quality_control: str  # "city", "developer", "joint"
    compatible_ownership: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "InfrastructureModel":
        """Create InfrastructureModel from a dictionary."""
        cost_data = data.get("cost_allocation", {})
        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            delivery_by=data.get("delivery_by", "city"),
            cost_allocation=InfrastructureCost.from_dict(cost_data),
            timing=data.get("timing", "before_construction"),
            quality_control=data.get("quality_control", "city"),
            compatible_ownership=data.get("compatible_ownership", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "delivery_by": self.delivery_by,
            "cost_allocation": self.cost_allocation.to_dict(),
            "timing": self.timing,
            "quality_control": self.quality_control,
            "compatible_ownership": self.compatible_ownership,
        }


@dataclass
class InfrastructureSet:
    """Collection of infrastructure models."""

    models: Dict[str, InfrastructureModel]

    def get(self, model_id: str) -> Optional[InfrastructureModel]:
        """Get an infrastructure model by ID."""
        return self.models.get(model_id)

    def get_city_delivered(self) -> List[InfrastructureModel]:
        """Get models where city delivers infrastructure."""
        return [m for m in self.models.values() if m.delivery_by == "city"]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InfrastructureSet":
        """Create InfrastructureSet from a dictionary."""
        models = {}
        infra_data = data.get("infrastructure_models", data)
        for model_id, model_data in infra_data.items():
            if isinstance(model_data, dict):
                models[model_id] = InfrastructureModel.from_dict(model_id, model_data)
        return cls(models=models)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "infrastructure_models": {
                mid: m.to_dict() for mid, m in self.models.items()
            }
        }
