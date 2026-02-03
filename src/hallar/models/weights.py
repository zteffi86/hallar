"""Weight profile definitions for Hallar DSS."""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class WeightProfile:
    """Weight profile for multi-objective utility calculation."""

    id: str
    name: str
    weights: Dict[str, float]  # objective -> weight

    REQUIRED_OBJECTIVES = ["speed", "affordability", "quality", "financial"]

    def __post_init__(self) -> None:
        # Validate all required objectives are present
        for obj in self.REQUIRED_OBJECTIVES:
            if obj not in self.weights:
                raise ValueError(f"Missing required objective: {obj}")

        # Validate weights are non-negative
        for obj, weight in self.weights.items():
            if weight < 0:
                raise ValueError(f"Weight for {obj} must be non-negative")

        # Normalize weights to sum to 1
        total = sum(self.weights.values())
        if total <= 0:
            raise ValueError("At least one weight must be positive")

        self.weights = {obj: w / total for obj, w in self.weights.items()}

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "WeightProfile":
        """Create WeightProfile from a dictionary."""
        return cls(
            id=id,
            name=data["name"],
            weights=data["weights"].copy(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "weights": self.weights.copy(),
        }

    @classmethod
    def create_custom(cls, speed: float, affordability: float, quality: float, financial: float) -> "WeightProfile":
        """Create a custom weight profile."""
        return cls(
            id="custom",
            name="Custom",
            weights={
                "speed": speed,
                "affordability": affordability,
                "quality": quality,
                "financial": financial,
            }
        )
