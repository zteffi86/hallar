"""Tests for expanded Hallar DSS models."""

import pytest
import yaml
from pathlib import Path

from hallar.models import (
    GoalSet,
    OwnershipSet,
    FinancingSet,
    ByggingarretturSet,
    InfrastructureSet,
    CounterpartySet,
    RiskCatalog,
    ComposedScenarioSet,
    HallarParameters,
)


DATA_DIR = Path(__file__).parent.parent / "data"


class TestGoalSet:
    """Tests for GoalSet model."""

    def test_load_goals(self):
        """Test loading goals from YAML."""
        with open(DATA_DIR / "goals.yaml") as f:
            data = yaml.safe_load(f)
        goals = GoalSet.from_dict(data)

        assert len(goals.goals) == 6
        assert "G1" in goals.goals
        assert goals.goals["G1"].name_en == "Speed"

    def test_presets(self):
        """Test loading weight presets."""
        with open(DATA_DIR / "goals.yaml") as f:
            data = yaml.safe_load(f)
        goals = GoalSet.from_dict(data)

        assert len(goals.presets) > 0
        assert "balanced" in goals.presets

        balanced = goals.presets["balanced"]
        total = sum(balanced.weights.values())
        assert 0.99 <= total <= 1.01


class TestOwnershipSet:
    """Tests for OwnershipSet model."""

    def test_load_ownership(self):
        """Test loading ownership structures from YAML."""
        with open(DATA_DIR / "ownership_structures.yaml") as f:
            data = yaml.safe_load(f)
        ownership = OwnershipSet.from_dict(data)

        assert len(ownership.structures) == 8
        assert "O1" in ownership.structures
        assert ownership.structures["O1"].name == "City Direct"


class TestFinancingSet:
    """Tests for FinancingSet model."""

    def test_load_financing(self):
        """Test loading financing models from YAML."""
        with open(DATA_DIR / "financing_models.yaml") as f:
            data = yaml.safe_load(f)
        financing = FinancingSet.from_dict(data)

        assert len(financing.models) == 8
        assert "F1" in financing.models


class TestByggingarretturSet:
    """Tests for ByggingarretturSet model."""

    def test_load_byggingarrettur(self):
        """Test loading byggingarrétt options from YAML."""
        with open(DATA_DIR / "byggingarrettur_options.yaml") as f:
            data = yaml.safe_load(f)
        bygg = ByggingarretturSet.from_dict(data)

        assert len(bygg.options) == 6
        assert "B1" in bygg.options
        assert bygg.options["B1"].name == "Market Sale"


class TestInfrastructureSet:
    """Tests for InfrastructureSet model."""

    def test_load_infrastructure(self):
        """Test loading infrastructure models from YAML."""
        with open(DATA_DIR / "infrastructure_models.yaml") as f:
            data = yaml.safe_load(f)
        infra = InfrastructureSet.from_dict(data)

        assert len(infra.models) == 6
        assert "I1" in infra.models


class TestCounterpartySet:
    """Tests for CounterpartySet model."""

    def test_load_counterparty(self):
        """Test loading counterparty profiles from YAML."""
        with open(DATA_DIR / "counterparty_profiles.yaml") as f:
            data = yaml.safe_load(f)
        counterparties = CounterpartySet.from_dict(data)

        assert len(counterparties.profiles) > 0

    def test_low_risk_counterparties(self):
        """Test filtering low-risk counterparties."""
        with open(DATA_DIR / "counterparty_profiles.yaml") as f:
            data = yaml.safe_load(f)
        counterparties = CounterpartySet.from_dict(data)

        low_risk = counterparties.get_low_risk(threshold=0.02)
        assert len(low_risk) > 0


class TestRiskCatalog:
    """Tests for RiskCatalog model."""

    def test_load_risks(self):
        """Test loading risk catalog from YAML."""
        with open(DATA_DIR / "risks.yaml") as f:
            data = yaml.safe_load(f)
        risks = RiskCatalog.from_dict(data)

        assert len(risks.risks) > 0


class TestComposedScenarioSet:
    """Tests for ComposedScenarioSet model."""

    def test_load_composed_scenarios(self):
        """Test loading composed scenarios from YAML."""
        with open(DATA_DIR / "composed_scenarios.yaml") as f:
            data = yaml.safe_load(f)
        scenarios = ComposedScenarioSet.from_dict(data)

        assert len(scenarios.scenarios) == 10
        assert "S01" in scenarios.scenarios
        assert scenarios.scenarios["S01"].name == "City Direct Development"

    def test_goal_scores(self):
        """Test that goal scores are loaded correctly."""
        with open(DATA_DIR / "composed_scenarios.yaml") as f:
            data = yaml.safe_load(f)
        scenarios = ComposedScenarioSet.from_dict(data)

        s01 = scenarios.scenarios["S01"]
        assert s01.goal_scores.speed == 30
        assert s01.goal_scores.affordability == 90
        assert s01.goal_scores.control == 100

    def test_filter_by_counterparty(self):
        """Test filtering scenarios by counterparty."""
        with open(DATA_DIR / "composed_scenarios.yaml") as f:
            data = yaml.safe_load(f)
        scenarios = ComposedScenarioSet.from_dict(data)

        city_scenarios = scenarios.get_by_counterparty("city")
        assert len(city_scenarios) > 0


class TestHallarParameters:
    """Tests for HallarParameters model."""

    def test_load_hallar_params(self):
        """Test loading Hallar parameters from YAML."""
        with open(DATA_DIR / "hallar_parameters.yaml") as f:
            data = yaml.safe_load(f)
        params = HallarParameters.from_dict(data)

        assert params.site.name == "Hallar"
        assert params.units.total_units == 3200
        assert params.infrastructure_costs.total.likely == 8000

    def test_byggingarrettur_valuation(self):
        """Test byggingarrétt valuation values."""
        with open(DATA_DIR / "hallar_parameters.yaml") as f:
            data = yaml.safe_load(f)
        params = HallarParameters.from_dict(data)

        assert params.byggingarrettur_valuation.total_value.likely == 16500
        assert params.byggingarrettur_valuation.total_value.min == 13500
        assert params.byggingarrettur_valuation.total_value.max == 21000
