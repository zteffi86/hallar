"""Byggingarrétt (development rights) disposition models for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from hallar.models.scenario import PERTParams


@dataclass
class ByggingarretturPricing:
    """Pricing parameters for byggingarrétt disposition."""

    method: str  # "market", "discounted", "agreed_valuation", "annual_payment", "value_equivalence", "mixed"
    discount: Optional[float] = None
    discount_range: Optional[PERTParams] = None
    expected_price: Optional[PERTParams] = None
    valuation_range: Optional[PERTParams] = None
    annual_rate: Optional[PERTParams] = None
    byggingarrettur_price: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ByggingarretturPricing":
        """Create ByggingarretturPricing from a dictionary."""
        discount_range = None
        if "discount_range" in data:
            discount_range = PERTParams.from_dict(data["discount_range"])

        expected_price = None
        if "expected_price" in data:
            expected_price = PERTParams.from_dict(data["expected_price"])

        valuation_range = None
        if "valuation_range" in data:
            valuation_range = PERTParams.from_dict(data["valuation_range"])

        annual_rate = None
        if "annual_rate" in data:
            annual_rate = PERTParams.from_dict(data["annual_rate"])

        return cls(
            method=data["method"],
            discount=data.get("discount"),
            discount_range=discount_range,
            expected_price=expected_price,
            valuation_range=valuation_range,
            annual_rate=annual_rate,
            byggingarrettur_price=data.get("byggingarrettur_price"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {"method": self.method}
        if self.discount is not None:
            result["discount"] = self.discount
        if self.discount_range is not None:
            result["discount_range"] = self.discount_range.to_dict()
        if self.expected_price is not None:
            result["expected_price"] = self.expected_price.to_dict()
        if self.valuation_range is not None:
            result["valuation_range"] = self.valuation_range.to_dict()
        if self.annual_rate is not None:
            result["annual_rate"] = self.annual_rate.to_dict()
        if self.byggingarrettur_price is not None:
            result["byggingarrettur_price"] = self.byggingarrettur_price
        return result


@dataclass
class CityReceives:
    """What the city receives from byggingarrétt disposition."""

    type: str  # "cash", "equity_stake", "annual_payments", "infrastructure"
    timing: str  # "upfront_or_staged", "returns_over_time", "yearly_for_lease_term", "upon_completion"
    certainty: str = "medium"  # "high", "medium", "uncertain"
    term_years: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CityReceives":
        """Create CityReceives from a dictionary."""
        return cls(
            type=data["type"],
            timing=data["timing"],
            certainty=data.get("certainty", "medium"),
            term_years=data.get("term_years"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "type": self.type,
            "timing": self.timing,
            "certainty": self.certainty,
        }
        if self.term_years is not None:
            result["term_years"] = self.term_years
        return result


@dataclass
class ByggingarretturOption:
    """A byggingarrétt (development rights) disposition option."""

    id: str
    name: str
    name_is: str
    description: str
    pricing: ByggingarretturPricing
    city_receives: CityReceives
    compatible_with: Dict[str, List[str]]  # {"ownership": [...], "financing": [...]}

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "ByggingarretturOption":
        """Create ByggingarretturOption from a dictionary."""
        # city_receives is optional - provide default for hybrid options
        city_receives_data = data.get("city_receives", {
            "type": "mixed",
            "timing": "varies",
            "certainty": "uncertain",
        })
        return cls(
            id=id,
            name=data["name"],
            name_is=data.get("name_is", data["name"]),
            description=data.get("description", ""),
            pricing=ByggingarretturPricing.from_dict(data["pricing"]),
            city_receives=CityReceives.from_dict(city_receives_data),
            compatible_with=data.get("compatible_with", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "name_is": self.name_is,
            "description": self.description,
            "pricing": self.pricing.to_dict(),
            "city_receives": self.city_receives.to_dict(),
            "compatible_with": self.compatible_with,
        }


@dataclass
class ByggingarretturSet:
    """Collection of byggingarrétt options."""

    options: Dict[str, ByggingarretturOption]
    reference_values: Dict[str, float] = field(default_factory=dict)

    def get(self, option_id: str) -> Optional[ByggingarretturOption]:
        """Get a byggingarrétt option by ID."""
        return self.options.get(option_id)

    def get_compatible_with_ownership(self, ownership_id: str) -> List[ByggingarretturOption]:
        """Get options compatible with an ownership structure."""
        return [
            opt for opt in self.options.values()
            if ownership_id in opt.compatible_with.get("ownership", [])
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ByggingarretturSet":
        """Create ByggingarretturSet from a dictionary."""
        options = {}
        options_data = data.get("byggingarrettur_options", {})
        for opt_id, opt_data in options_data.items():
            if isinstance(opt_data, dict):
                options[opt_id] = ByggingarretturOption.from_dict(opt_id, opt_data)
        return cls(
            options=options,
            reference_values=data.get("reference_values", {}),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reference_values": self.reference_values,
            "byggingarrettur_options": {
                oid: o.to_dict() for oid, o in self.options.items()
            },
        }
