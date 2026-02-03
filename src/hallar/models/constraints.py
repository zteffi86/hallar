"""Constraint definitions for Hallar DSS."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Tuple, Optional
import numpy as np


class ConstraintType(Enum):
    """Types of constraints."""

    PROBABILISTIC = "probabilistic"  # P(metric >= threshold) must be >= confidence
    CVAR = "cvar"  # CVaR at alpha must be >= threshold
    DEADLINE = "deadline"  # P(metric <= threshold) must be >= confidence
    MINIMUM = "minimum"  # Deterministic minimum value
    MAXIMUM = "maximum"  # Deterministic maximum value
    CATEGORICAL = "categorical"  # Value must be in allowed set


@dataclass
class Constraint:
    """Single constraint definition."""

    id: str
    name: str
    type: ConstraintType
    metric: str
    threshold: Any  # Numeric for most, string/list for categorical
    confidence: Optional[float] = None  # Required for probabilistic/deadline
    alpha: Optional[float] = None  # Required for CVaR
    allowed_values: Optional[List[str]] = None  # Required for categorical

    def __post_init__(self) -> None:
        if self.type in [ConstraintType.PROBABILISTIC, ConstraintType.DEADLINE]:
            if self.confidence is None:
                raise ValueError(f"{self.type.value} constraint requires confidence level")
            if not 0 <= self.confidence <= 1:
                raise ValueError("confidence must be between 0 and 1")

        if self.type == ConstraintType.CVAR:
            if self.alpha is None:
                raise ValueError("CVaR constraint requires alpha level")
            if not 0 < self.alpha <= 1:
                raise ValueError("alpha must be between 0 and 1")

        if self.type == ConstraintType.CATEGORICAL:
            if self.allowed_values is None or len(self.allowed_values) == 0:
                raise ValueError("Categorical constraint requires allowed_values")

    @classmethod
    def from_dict(cls, id: str, data: Dict[str, Any]) -> "Constraint":
        """Create Constraint from a dictionary."""
        return cls(
            id=id,
            name=data["name"],
            type=ConstraintType(data["type"]),
            metric=data["metric"],
            threshold=data["threshold"],
            confidence=data.get("confidence"),
            alpha=data.get("alpha"),
            allowed_values=data.get("allowed_values"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "name": self.name,
            "type": self.type.value,
            "metric": self.metric,
            "threshold": self.threshold,
        }
        if self.confidence is not None:
            result["confidence"] = self.confidence
        if self.alpha is not None:
            result["alpha"] = self.alpha
        if self.allowed_values is not None:
            result["allowed_values"] = self.allowed_values
        return result

    def check(self, metric_values: Any) -> Tuple[bool, str]:
        """
        Check if the constraint is satisfied.

        Args:
            metric_values: For probabilistic/cvar/deadline: numpy array of simulated values
                          For minimum/maximum/categorical: single value

        Returns:
            Tuple of (passed: bool, message: str)
        """
        if self.type == ConstraintType.PROBABILISTIC:
            # P(metric >= threshold) must be >= confidence
            prob_satisfied = np.mean(metric_values >= self.threshold)
            passed = prob_satisfied >= self.confidence
            msg = f"P(>={self.threshold}) = {prob_satisfied:.1%} {'≥' if passed else '<'} {self.confidence:.0%}"
            return passed, msg

        elif self.type == ConstraintType.CVAR:
            # CVaR at alpha must be >= threshold
            cutoff = np.percentile(metric_values, self.alpha * 100)
            cvar = np.mean(metric_values[metric_values <= cutoff])
            passed = cvar >= self.threshold
            msg = f"CVaR({self.alpha:.0%}) = {cvar:.0f} {'≥' if passed else '<'} {self.threshold}"
            return passed, msg

        elif self.type == ConstraintType.DEADLINE:
            # P(metric <= threshold) must be >= confidence
            prob_on_time = np.mean(metric_values <= self.threshold)
            passed = prob_on_time >= self.confidence
            msg = f"P(<={self.threshold}) = {prob_on_time:.1%} {'≥' if passed else '<'} {self.confidence:.0%}"
            return passed, msg

        elif self.type == ConstraintType.MINIMUM:
            # Deterministic minimum
            passed = metric_values >= self.threshold
            msg = f"{metric_values} {'≥' if passed else '<'} {self.threshold}"
            return passed, msg

        elif self.type == ConstraintType.MAXIMUM:
            # Deterministic maximum
            passed = metric_values <= self.threshold
            msg = f"{metric_values} {'≤' if passed else '>'} {self.threshold}"
            return passed, msg

        elif self.type == ConstraintType.CATEGORICAL:
            # Value must be in allowed set
            passed = metric_values in self.allowed_values
            msg = f"{metric_values} {'∈' if passed else '∉'} {self.allowed_values}"
            return passed, msg

        else:
            raise ValueError(f"Unknown constraint type: {self.type}")


@dataclass
class ConstraintSet:
    """Collection of constraints."""

    constraints: Dict[str, Constraint] = field(default_factory=dict)

    def add(self, constraint: Constraint) -> None:
        """Add a constraint to the set."""
        self.constraints[constraint.id] = constraint

    def check_all(
        self,
        simulation_results: Dict[str, Any],
        deterministic_values: Dict[str, Any]
    ) -> Tuple[bool, List[Tuple[str, str]]]:
        """
        Check all constraints against simulation results.

        Args:
            simulation_results: Dict mapping metric names to numpy arrays of simulated values
            deterministic_values: Dict mapping metric names to single values

        Returns:
            Tuple of (all_passed: bool, violations: List[Tuple[constraint_id, message]])
        """
        violations = []

        for constraint_id, constraint in self.constraints.items():
            # Get the metric values
            if constraint.type in [ConstraintType.MINIMUM, ConstraintType.MAXIMUM, ConstraintType.CATEGORICAL]:
                if constraint.metric not in deterministic_values:
                    violations.append((constraint_id, f"Missing metric: {constraint.metric}"))
                    continue
                values = deterministic_values[constraint.metric]
            else:
                if constraint.metric not in simulation_results:
                    violations.append((constraint_id, f"Missing metric: {constraint.metric}"))
                    continue
                values = simulation_results[constraint.metric]

            passed, msg = constraint.check(values)
            if not passed:
                violations.append((constraint_id, f"{constraint.name}: {msg}"))

        return len(violations) == 0, violations

    @classmethod
    def from_dict(cls, data: Dict[str, Dict[str, Any]]) -> "ConstraintSet":
        """Create ConstraintSet from a dictionary."""
        constraint_set = cls()
        for id, constraint_data in data.items():
            constraint_set.add(Constraint.from_dict(id, constraint_data))
        return constraint_set

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Convert to dictionary."""
        return {id: c.to_dict() for id, c in self.constraints.items()}
