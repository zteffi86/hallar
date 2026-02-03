"""Counterparty risk profile models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from hallar.models.scenario import PERTParams


@dataclass
class CounterpartyProfile:
    """Risk profile for a counterparty type."""

    id: str
    name: str
    name_is: str
    description: str
    category: str  # "pension_fund", "developer", "city_entity", "mixed"
    default_probability: PERTParams
    recovery_rate: float  # 0-1, expected recovery if default occurs
    financial_strength: str  # "very_strong", "strong", "moderate", "weak"
    track_record: str  # "excellent", "good", "limited", "poor"
    risk_factors: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0 <= self.recovery_rate <= 1:
            raise ValueError(f"recovery_rate must be between 0 and 1, got {self.recovery_rate}")

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "CounterpartyProfile":
        """Create CounterpartyProfile from a dictionary."""
        default_prob_data = data.get("default_probability", {"min": 0.01, "likely": 0.05, "max": 0.10})

        # Handle recovery_rate - can be float or PERT dict
        recovery_data = data.get("recovery_rate", 0.5)
        if isinstance(recovery_data, dict):
            recovery_rate = recovery_data.get("likely", 0.5)
        else:
            recovery_rate = recovery_data

        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            category=data.get("category", "developer"),
            default_probability=PERTParams.from_dict(default_prob_data),
            recovery_rate=recovery_rate,
            financial_strength=data.get("financial_strength", "moderate"),
            track_record=data.get("track_record", "limited"),
            risk_factors=data.get("risk_factors", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "category": self.category,
            "default_probability": self.default_probability.to_dict(),
            "recovery_rate": self.recovery_rate,
            "financial_strength": self.financial_strength,
            "track_record": self.track_record,
            "risk_factors": self.risk_factors,
        }


@dataclass
class CounterpartySet:
    """Collection of counterparty profiles."""

    profiles: Dict[str, CounterpartyProfile]

    def get(self, profile_id: str) -> Optional[CounterpartyProfile]:
        """Get a counterparty profile by ID."""
        return self.profiles.get(profile_id)

    def get_by_category(self, category: str) -> List[CounterpartyProfile]:
        """Get profiles by category."""
        return [p for p in self.profiles.values() if p.category == category]

    def get_low_risk(self, threshold: float = 0.02) -> List[CounterpartyProfile]:
        """Get profiles with low default probability (likely < threshold)."""
        return [
            p for p in self.profiles.values()
            if p.default_probability.likely < threshold
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CounterpartySet":
        """Create CounterpartySet from a dictionary."""
        profiles = {}
        profile_data = data.get("counterparty_profiles", data)
        for prof_id, prof_data in profile_data.items():
            if isinstance(prof_data, dict):
                profiles[prof_id] = CounterpartyProfile.from_dict(prof_id, prof_data)
        return cls(profiles=profiles)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "counterparty_profiles": {
                pid: p.to_dict() for pid, p in self.profiles.items()
            }
        }
