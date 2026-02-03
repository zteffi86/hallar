"""Tests for constraint checking."""

import pytest
import numpy as np
from hallar.models.constraints import Constraint, ConstraintSet, ConstraintType


class TestConstraint:
    """Tests for individual constraints."""

    def test_probabilistic_constraint_pass(self):
        """Probabilistic constraint should pass when confidence met."""
        constraint = Constraint(
            id="test",
            name="Test constraint",
            type=ConstraintType.PROBABILISTIC,
            metric="npv",
            threshold=0,
            confidence=0.90,
        )

        # 95% of values are positive
        values = np.concatenate([np.ones(950) * 100, np.ones(50) * -10])
        passed, msg = constraint.check(values)

        assert passed
        assert "95.0%" in msg

    def test_probabilistic_constraint_fail(self):
        """Probabilistic constraint should fail when confidence not met."""
        constraint = Constraint(
            id="test",
            name="Test constraint",
            type=ConstraintType.PROBABILISTIC,
            metric="npv",
            threshold=0,
            confidence=0.90,
        )

        # Only 80% positive
        values = np.concatenate([np.ones(800) * 100, np.ones(200) * -10])
        passed, msg = constraint.check(values)

        assert not passed
        assert "80.0%" in msg

    def test_cvar_constraint_pass(self):
        """CVaR constraint should pass when threshold met."""
        constraint = Constraint(
            id="test",
            name="Test CVaR",
            type=ConstraintType.CVAR,
            metric="npv",
            threshold=-1000,
            alpha=0.05,
        )

        # CVaR (worst 5%) should be above -1000
        values = np.concatenate([np.ones(950) * 100, np.ones(50) * -500])
        passed, msg = constraint.check(values)

        assert passed

    def test_cvar_constraint_fail(self):
        """CVaR constraint should fail when threshold not met."""
        constraint = Constraint(
            id="test",
            name="Test CVaR",
            type=ConstraintType.CVAR,
            metric="npv",
            threshold=-500,
            alpha=0.05,
        )

        # CVaR (worst 5%) will be around -2000
        values = np.concatenate([np.ones(950) * 100, np.ones(50) * -2000])
        passed, msg = constraint.check(values)

        assert not passed

    def test_deadline_constraint_pass(self):
        """Deadline constraint should pass when on-time probability met."""
        constraint = Constraint(
            id="test",
            name="School timing",
            type=ConstraintType.DEADLINE,
            metric="first_school_months",
            threshold=60,
            confidence=0.80,
        )

        # 85% complete within 60 months
        values = np.concatenate([np.ones(850) * 50, np.ones(150) * 80])
        passed, msg = constraint.check(values)

        assert passed

    def test_deadline_constraint_fail(self):
        """Deadline constraint should fail when on-time probability not met."""
        constraint = Constraint(
            id="test",
            name="School timing",
            type=ConstraintType.DEADLINE,
            metric="first_school_months",
            threshold=60,
            confidence=0.80,
        )

        # Only 70% complete within 60 months
        values = np.concatenate([np.ones(700) * 50, np.ones(300) * 80])
        passed, msg = constraint.check(values)

        assert not passed

    def test_minimum_constraint_pass(self):
        """Minimum constraint should pass when value exceeds threshold."""
        constraint = Constraint(
            id="test",
            name="Min affordable",
            type=ConstraintType.MINIMUM,
            metric="affordable_percentage",
            threshold=0.25,
        )

        passed, msg = constraint.check(0.30)
        assert passed

    def test_minimum_constraint_fail(self):
        """Minimum constraint should fail when value below threshold."""
        constraint = Constraint(
            id="test",
            name="Min affordable",
            type=ConstraintType.MINIMUM,
            metric="affordable_percentage",
            threshold=0.25,
        )

        passed, msg = constraint.check(0.20)
        assert not passed

    def test_categorical_constraint_pass(self):
        """Categorical constraint should pass when value in allowed set."""
        constraint = Constraint(
            id="test",
            name="Energy rating",
            type=ConstraintType.CATEGORICAL,
            metric="energy_rating",
            threshold="A",
            allowed_values=["A+", "A"],
        )

        passed, msg = constraint.check("A")
        assert passed

    def test_categorical_constraint_fail(self):
        """Categorical constraint should fail when value not in allowed set."""
        constraint = Constraint(
            id="test",
            name="Energy rating",
            type=ConstraintType.CATEGORICAL,
            metric="energy_rating",
            threshold="A",
            allowed_values=["A+", "A"],
        )

        passed, msg = constraint.check("B")
        assert not passed

    def test_constraint_validation_probabilistic_requires_confidence(self):
        """Probabilistic constraint should require confidence."""
        with pytest.raises(ValueError, match="confidence"):
            Constraint(
                id="test",
                name="Test",
                type=ConstraintType.PROBABILISTIC,
                metric="npv",
                threshold=0,
            )

    def test_constraint_validation_cvar_requires_alpha(self):
        """CVaR constraint should require alpha."""
        with pytest.raises(ValueError, match="alpha"):
            Constraint(
                id="test",
                name="Test",
                type=ConstraintType.CVAR,
                metric="npv",
                threshold=-1000,
            )


class TestConstraintSet:
    """Tests for constraint set."""

    def test_constraint_set_all_pass(self):
        """All constraints pass."""
        cs = ConstraintSet()
        cs.add(Constraint(
            id="min_afford",
            name="Min affordable",
            type=ConstraintType.MINIMUM,
            metric="affordable_percentage",
            threshold=0.25,
        ))
        cs.add(Constraint(
            id="energy",
            name="Energy",
            type=ConstraintType.CATEGORICAL,
            metric="energy_rating",
            threshold="A",
            allowed_values=["A+", "A"],
        ))

        sim_results = {}
        deterministic = {
            "affordable_percentage": 0.30,
            "energy_rating": "A",
        }

        passed, violations = cs.check_all(sim_results, deterministic)
        assert passed
        assert len(violations) == 0

    def test_constraint_set_some_fail(self):
        """Some constraints fail."""
        cs = ConstraintSet()
        cs.add(Constraint(
            id="min_afford",
            name="Min affordable",
            type=ConstraintType.MINIMUM,
            metric="affordable_percentage",
            threshold=0.25,
        ))
        cs.add(Constraint(
            id="energy",
            name="Energy",
            type=ConstraintType.CATEGORICAL,
            metric="energy_rating",
            threshold="A",
            allowed_values=["A+", "A"],
        ))

        sim_results = {}
        deterministic = {
            "affordable_percentage": 0.20,  # Fails
            "energy_rating": "A",            # Passes
        }

        passed, violations = cs.check_all(sim_results, deterministic)
        assert not passed
        assert len(violations) == 1
        assert "min_afford" in violations[0][0]

    def test_constraint_set_from_dict(self):
        """Create constraint set from dictionary."""
        data = {
            "financial": {
                "name": "Must not lose",
                "type": "probabilistic",
                "metric": "npv",
                "threshold": 0,
                "confidence": 0.90,
            },
            "timing": {
                "name": "School timing",
                "type": "deadline",
                "metric": "first_school_months",
                "threshold": 60,
                "confidence": 0.80,
            },
        }

        cs = ConstraintSet.from_dict(data)
        assert len(cs.constraints) == 2
        assert "financial" in cs.constraints
        assert "timing" in cs.constraints
