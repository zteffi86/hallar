"""Goal and weight models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum


class GoalDirection(Enum):
    """Direction of optimization for a goal."""
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


@dataclass
class Goal:
    """A single goal/objective for scenario evaluation."""

    id: str
    name: str
    name_en: str
    description: str
    description_en: str
    icon: str
    metrics: List[str]
    direction: GoalDirection

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "Goal":
        """Create Goal from a dictionary."""
        return cls(
            id=id,
            name=data["name"],
            name_en=data["name_en"],
            description=data["description"],
            description_en=data["description_en"],
            icon=data.get("icon", ""),
            metrics=data.get("metrics", []),
            direction=GoalDirection(data.get("direction", "maximize")),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_en": self.name_en,
            "description": self.description,
            "description_en": self.description_en,
            "icon": self.icon,
            "metrics": self.metrics,
            "direction": self.direction.value,
        }


@dataclass
class WeightPreset:
    """A preset weight configuration for goals."""

    id: str
    name: str
    name_en: str
    description: str
    weights: Dict[str, float]

    def __post_init__(self) -> None:
        # Validate weights sum to approximately 1
        total = sum(self.weights.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Weights must sum to 1, got {total}")

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "WeightPreset":
        """Create WeightPreset from a dictionary."""
        return cls(
            id=id,
            name=data["name"],
            name_en=data["name_en"],
            description=data.get("description", ""),
            weights=data["weights"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_en": self.name_en,
            "description": self.description,
            "weights": self.weights,
        }


@dataclass
class GoalSet:
    """Collection of goals with weight presets."""

    goals: Dict[str, Goal]
    presets: Dict[str, WeightPreset]

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """Get a goal by ID."""
        return self.goals.get(goal_id)

    def get_preset(self, preset_id: str) -> Optional[WeightPreset]:
        """Get a weight preset by ID."""
        return self.presets.get(preset_id)

    def get_goal_ids(self) -> List[str]:
        """Get list of all goal IDs."""
        return list(self.goals.keys())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalSet":
        """Create GoalSet from a dictionary."""
        goals = {}
        for goal_id, goal_data in data.get("goals", {}).items():
            goals[goal_id] = Goal.from_dict(goal_id, goal_data)

        presets = {}
        for preset_id, preset_data in data.get("presets", {}).items():
            presets[preset_id] = WeightPreset.from_dict(preset_id, preset_data)

        return cls(goals=goals, presets=presets)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "goals": {gid: g.to_dict() for gid, g in self.goals.items()},
            "presets": {pid: p.to_dict() for pid, p in self.presets.items()},
        }
