"""Ownership structure models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class OwnershipStructure:
    """An ownership structure option for land development."""

    id: str
    name: str
    name_is: str
    description: str
    city_role: str
    counterparty: str
    city_control: float  # 0-100
    risk_allocation: Dict[str, str]  # e.g., {"construction": "city", "market": "developer"}
    compatible_financing: List[str]
    compatible_byggingarrettur: List[str]

    def __post_init__(self) -> None:
        if not 0 <= self.city_control <= 100:
            raise ValueError(f"city_control must be between 0 and 100, got {self.city_control}")

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "OwnershipStructure":
        """Create OwnershipStructure from a dictionary."""
        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            city_role=data.get("city_role", ""),
            counterparty=data.get("counterparty", ""),
            city_control=data.get("city_control", 50),
            risk_allocation=data.get("risk_allocation", {}),
            compatible_financing=data.get("compatible_financing", []),
            compatible_byggingarrettur=data.get("compatible_byggingarrettur", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "city_role": self.city_role,
            "counterparty": self.counterparty,
            "city_control": self.city_control,
            "risk_allocation": self.risk_allocation,
            "compatible_financing": self.compatible_financing,
            "compatible_byggingarrettur": self.compatible_byggingarrettur,
        }


@dataclass
class OwnershipSet:
    """Collection of ownership structures."""

    structures: Dict[str, OwnershipStructure]

    def get(self, structure_id: str) -> Optional[OwnershipStructure]:
        """Get an ownership structure by ID."""
        return self.structures.get(structure_id)

    def get_compatible_with_financing(self, financing_id: str) -> List[OwnershipStructure]:
        """Get ownership structures compatible with a financing model."""
        return [
            s for s in self.structures.values()
            if financing_id in s.compatible_financing
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OwnershipSet":
        """Create OwnershipSet from a dictionary."""
        structures = {}
        ownership_data = data.get("ownership_structures", data)
        for struct_id, struct_data in ownership_data.items():
            if isinstance(struct_data, dict):
                structures[struct_id] = OwnershipStructure.from_dict(struct_id, struct_data)
        return cls(structures=structures)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ownership_structures": {
                sid: s.to_dict() for sid, s in self.structures.items()
            }
        }
