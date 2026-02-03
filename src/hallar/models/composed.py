"""Composed scenario models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union

from hallar.models.scenario import PERTParams


@dataclass
class ScenarioComponents:
    """Component IDs that make up a composed scenario."""

    ownership: str  # O1-O8
    financing: str  # F1-F8
    byggingarrettur: str  # B1-B6 or "N/A"
    infrastructure: str  # I1-I6

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioComponents":
        """Create ScenarioComponents from a dictionary."""
        return cls(
            ownership=data["ownership"],
            financing=data["financing"],
            byggingarrettur=data.get("byggingarrettur", "N/A"),
            infrastructure=data["infrastructure"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "ownership": self.ownership,
            "financing": self.financing,
            "byggingarrettur": self.byggingarrettur,
            "infrastructure": self.infrastructure,
        }


@dataclass
class GoalScores:
    """Pre-defined goal scores for a composed scenario."""

    speed: int  # 0-100
    affordability: int
    quality: int
    financial: int
    risk: int
    control: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalScores":
        """Create GoalScores from a dictionary."""
        return cls(
            speed=data.get("speed", 50),
            affordability=data.get("affordability", 50),
            quality=data.get("quality", 50),
            financial=data.get("financial", 50),
            risk=data.get("risk", 50),
            control=data.get("control", 50),
        )

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "speed": self.speed,
            "affordability": self.affordability,
            "quality": self.quality,
            "financial": self.financial,
            "risk": self.risk,
            "control": self.control,
        }

    def as_list(self) -> List[int]:
        """Return scores as ordered list."""
        return [self.speed, self.affordability, self.quality,
                self.financial, self.risk, self.control]


@dataclass
class EquityStructure:
    """Equity ownership structure for JV scenarios."""

    city_share: float
    pension_share: float = 0.0
    developer_share: float = 0.0

    def __post_init__(self) -> None:
        total = self.city_share + self.pension_share + self.developer_share
        if total > 0 and not 0.99 <= total <= 1.01:
            raise ValueError(f"Equity shares must sum to 1, got {total}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EquityStructure":
        """Create EquityStructure from a dictionary."""
        return cls(
            city_share=data.get("city_share", 0.0),
            pension_share=data.get("pension_share", 0.0),
            developer_share=data.get("developer_share", 0.0),
        )

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        result = {"city_share": self.city_share}
        if self.pension_share > 0:
            result["pension_share"] = self.pension_share
        if self.developer_share > 0:
            result["developer_share"] = self.developer_share
        return result


@dataclass
class AffordabilityCommitment:
    """Affordability commitment for a scenario."""

    minimum_pct: float  # Minimum percentage of affordable units
    discount_depth: float = 0.0  # Discount from market price
    restriction_years: int = 0  # Years commitment is binding
    rental_pct: float = 0.0  # Percentage that must be rental

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AffordabilityCommitment":
        """Create AffordabilityCommitment from a dictionary."""
        return cls(
            minimum_pct=data.get("minimum_pct", 0.0),
            discount_depth=data.get("discount_depth", 0.0),
            restriction_years=data.get("restriction_years", 0),
            rental_pct=data.get("rental_pct", 0.0),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "minimum_pct": self.minimum_pct,
            "discount_depth": self.discount_depth,
            "restriction_years": self.restriction_years,
            "rental_pct": self.rental_pct,
        }


@dataclass
class PhaseStructure:
    """Structure for a single phase in phased scenarios."""

    units: int
    structure: str  # Reference to another scenario ID

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseStructure":
        """Create PhaseStructure from a dictionary."""
        return cls(
            units=data["units"],
            structure=data["structure"],
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"units": self.units, "structure": self.structure}


@dataclass
class ComposedScenario:
    """A fully composed scenario combining ownership, financing, etc."""

    id: str
    name: str
    name_is: str
    description: str
    components: ScenarioComponents
    counterparty: str
    default_probability: Union[float, PERTParams]
    city_control_score: int  # 0-100
    goal_scores: GoalScores
    equity_structure: Optional[EquityStructure] = None
    affordability_commitment: Optional[AffordabilityCommitment] = None
    phases: Optional[Dict[str, PhaseStructure]] = None

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "ComposedScenario":
        """Create ComposedScenario from a dictionary."""
        # Parse default probability (can be float or PERT)
        default_prob_data = data.get("default_probability", 0.05)
        if isinstance(default_prob_data, dict):
            if "overall" in default_prob_data:
                default_prob = default_prob_data["overall"]
            else:
                default_prob = PERTParams.from_dict(default_prob_data)
        else:
            default_prob = default_prob_data

        # Parse optional equity structure
        equity = None
        if "equity_structure" in data:
            equity = EquityStructure.from_dict(data["equity_structure"])

        # Parse optional affordability commitment
        affordability = None
        if "affordability_commitment" in data:
            affordability = AffordabilityCommitment.from_dict(data["affordability_commitment"])

        # Parse optional phases
        phases = None
        if "phases" in data:
            phases = {}
            for phase_name, phase_data in data["phases"].items():
                phases[phase_name] = PhaseStructure.from_dict(phase_data)

        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            components=ScenarioComponents.from_dict(data["components"]),
            counterparty=data.get("counterparty", "unknown"),
            default_probability=default_prob,
            city_control_score=data.get("city_control_score", 50),
            goal_scores=GoalScores.from_dict(data.get("goal_scores", {})),
            equity_structure=equity,
            affordability_commitment=affordability,
            phases=phases,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "components": self.components.to_dict(),
            "counterparty": self.counterparty,
            "city_control_score": self.city_control_score,
            "goal_scores": self.goal_scores.to_dict(),
        }

        if isinstance(self.default_probability, PERTParams):
            result["default_probability"] = self.default_probability.to_dict()
        else:
            result["default_probability"] = self.default_probability

        if self.equity_structure is not None:
            result["equity_structure"] = self.equity_structure.to_dict()
        if self.affordability_commitment is not None:
            result["affordability_commitment"] = self.affordability_commitment.to_dict()
        if self.phases is not None:
            result["phases"] = {k: v.to_dict() for k, v in self.phases.items()}

        return result

    def get_default_probability_likely(self) -> float:
        """Get the likely default probability value."""
        if isinstance(self.default_probability, PERTParams):
            return self.default_probability.likely
        return self.default_probability


@dataclass
class ComposedScenarioSet:
    """Collection of composed scenarios."""

    scenarios: Dict[str, ComposedScenario]
    selection_guide: Dict[str, List[str]] = field(default_factory=dict)

    def get(self, scenario_id: str) -> Optional[ComposedScenario]:
        """Get a scenario by ID."""
        return self.scenarios.get(scenario_id)

    def get_by_counterparty(self, counterparty: str) -> List[ComposedScenario]:
        """Get scenarios by counterparty type."""
        return [s for s in self.scenarios.values() if s.counterparty == counterparty]

    def get_low_risk(self, threshold: float = 0.05) -> List[ComposedScenario]:
        """Get scenarios with low default probability."""
        return [
            s for s in self.scenarios.values()
            if s.get_default_probability_likely() < threshold
        ]

    def get_high_control(self, threshold: int = 50) -> List[ComposedScenario]:
        """Get scenarios with high city control."""
        return [
            s for s in self.scenarios.values()
            if s.city_control_score >= threshold
        ]

    def get_recommended_for_goal(self, goal: str) -> List[str]:
        """Get recommended scenario IDs for a goal priority."""
        return self.selection_guide.get(f"by_goal_priority", {}).get(goal, [])

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComposedScenarioSet":
        """Create ComposedScenarioSet from a dictionary."""
        scenarios = {}
        scenario_data = data.get("composed_scenarios", {})
        for scen_id, scen_info in scenario_data.items():
            if isinstance(scen_info, dict):
                scenarios[scen_id] = ComposedScenario.from_dict(scen_id, scen_info)

        selection_guide = data.get("selection_guide", {})

        return cls(scenarios=scenarios, selection_guide=selection_guide)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "composed_scenarios": {
                sid: s.to_dict() for sid, s in self.scenarios.items()
            },
            "selection_guide": self.selection_guide,
        }
