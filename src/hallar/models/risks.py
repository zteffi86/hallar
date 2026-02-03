"""Risk catalog models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from hallar.models.scenario import PERTParams


@dataclass
class RiskImpact:
    """Impact parameters for a risk event."""

    cost_increase_pct: Optional[PERTParams] = None  # % increase in costs
    delay_months: Optional[PERTParams] = None  # Additional delay
    revenue_decrease_pct: Optional[PERTParams] = None  # % decrease in revenue
    npv_impact: Optional[PERTParams] = None  # Direct NPV impact in M ISK

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskImpact":
        """Create RiskImpact from a dictionary."""
        cost_increase = None
        if "cost_increase_pct" in data:
            cost_increase = PERTParams.from_dict(data["cost_increase_pct"])

        delay = None
        if "delay_months" in data:
            delay = PERTParams.from_dict(data["delay_months"])

        revenue_decrease = None
        if "revenue_decrease_pct" in data:
            revenue_decrease = PERTParams.from_dict(data["revenue_decrease_pct"])

        npv = None
        if "npv_impact" in data:
            npv = PERTParams.from_dict(data["npv_impact"])

        return cls(
            cost_increase_pct=cost_increase,
            delay_months=delay,
            revenue_decrease_pct=revenue_decrease,
            npv_impact=npv,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {}
        if self.cost_increase_pct is not None:
            result["cost_increase_pct"] = self.cost_increase_pct.to_dict()
        if self.delay_months is not None:
            result["delay_months"] = self.delay_months.to_dict()
        if self.revenue_decrease_pct is not None:
            result["revenue_decrease_pct"] = self.revenue_decrease_pct.to_dict()
        if self.npv_impact is not None:
            result["npv_impact"] = self.npv_impact.to_dict()
        return result


@dataclass
class Risk:
    """A risk event in the risk catalog."""

    id: str
    name: str
    name_is: str
    description: str
    category: str  # "construction", "market", "counterparty", "regulatory", "political"
    probability: PERTParams
    impact: RiskImpact
    mitigations: List[str] = field(default_factory=list)
    affected_scenarios: List[str] = field(default_factory=list)
    correlation_with: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "Risk":
        """Create Risk from a dictionary."""
        # Handle both old "probability"/"impact" structure and new "quantification" structure
        if "probability" in data:
            probability = PERTParams.from_dict(data["probability"])
            impact = RiskImpact.from_dict(data.get("impact", {}))
        elif "quantification" in data:
            quant = data["quantification"]
            # Extract base probability from quantification
            base_prob_data = quant.get("base_probability", 0.1)
            # base_probability can be float or dict (by counterparty type)
            if isinstance(base_prob_data, dict):
                # Take average of all counterparty types
                base_prob = sum(base_prob_data.values()) / len(base_prob_data) if base_prob_data else 0.1
            else:
                base_prob = base_prob_data
            probability = PERTParams(min=base_prob * 0.5, likely=base_prob, max=min(1.0, base_prob * 2))

            # Extract impact from impact_range
            impact_range = quant.get("impact_range", {})
            impact_type = quant.get("impact_type", "")

            if impact_type == "cost_multiplier" and impact_range:
                # Convert cost multiplier to cost increase percentage
                impact = RiskImpact(
                    cost_increase_pct=PERTParams(
                        min=(impact_range.get("min", 1.0) - 1) * 100,
                        likely=(impact_range.get("likely", 1.1) - 1) * 100,
                        max=(impact_range.get("max", 1.5) - 1) * 100,
                    )
                )
            elif impact_type == "delay_months" and impact_range:
                impact = RiskImpact(
                    delay_months=PERTParams.from_dict(impact_range)
                )
            else:
                impact = RiskImpact()
        else:
            # Default values
            probability = PERTParams(min=0.05, likely=0.1, max=0.2)
            impact = RiskImpact()

        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            category=data.get("category", "other"),
            probability=probability,
            impact=impact,
            mitigations=data.get("mitigations", []),
            affected_scenarios=data.get("affected_scenarios", []),
            correlation_with=data.get("correlation_with", []),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "category": self.category,
            "probability": self.probability.to_dict(),
            "impact": self.impact.to_dict(),
            "mitigations": self.mitigations,
            "affected_scenarios": self.affected_scenarios,
            "correlation_with": self.correlation_with,
        }


@dataclass
class RiskCatalog:
    """Collection of risk definitions."""

    risks: Dict[str, Risk]

    def get(self, risk_id: str) -> Optional[Risk]:
        """Get a risk by ID."""
        return self.risks.get(risk_id)

    def get_by_category(self, category: str) -> List[Risk]:
        """Get risks by category."""
        return [r for r in self.risks.values() if r.category == category]

    def get_high_probability(self, threshold: float = 0.3) -> List[Risk]:
        """Get risks with high probability (likely > threshold)."""
        return [
            r for r in self.risks.values()
            if r.probability.likely > threshold
        ]

    def get_affecting_scenario(self, scenario_id: str) -> List[Risk]:
        """Get risks that affect a specific scenario."""
        return [
            r for r in self.risks.values()
            if scenario_id in r.affected_scenarios or not r.affected_scenarios
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskCatalog":
        """Create RiskCatalog from a dictionary."""
        risks = {}
        risk_data = data.get("risks", data)
        for risk_id, risk_info in risk_data.items():
            if isinstance(risk_info, dict):
                risks[risk_id] = Risk.from_dict(risk_id, risk_info)
        return cls(risks=risks)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "risks": {rid: r.to_dict() for rid, r in self.risks.items()}
        }
