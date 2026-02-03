"""Tests for data models."""

import pytest
from hallar.models.scenario import (
    PERTParams, RiskParams, AffordabilityParams, QualityParams,
    JVParams, TimelineParams, Scenario,
)
from hallar.models.market import MarketScenario, MarketParams
from hallar.models.weights import WeightProfile


class TestPERTParams:
    """Tests for PERTParams dataclass."""

    def test_valid_params(self):
        """Valid PERT parameters should work."""
        params = PERTParams(min=10, likely=15, max=20)
        assert params.min == 10
        assert params.likely == 15
        assert params.max == 20

    def test_min_equals_likely(self):
        """min == likely is valid."""
        params = PERTParams(min=10, likely=10, max=20)
        assert params.min == params.likely

    def test_likely_equals_max(self):
        """likely == max is valid."""
        params = PERTParams(min=10, likely=20, max=20)
        assert params.likely == params.max

    def test_all_equal(self):
        """All equal values is valid."""
        params = PERTParams(min=15, likely=15, max=15)
        assert params.min == params.likely == params.max

    def test_invalid_min_greater_than_likely(self):
        """min > likely should raise error."""
        with pytest.raises(ValueError):
            PERTParams(min=20, likely=15, max=25)

    def test_invalid_likely_greater_than_max(self):
        """likely > max should raise error."""
        with pytest.raises(ValueError):
            PERTParams(min=10, likely=25, max=20)

    def test_from_dict(self):
        """Create from dictionary."""
        data = {"min": 10, "likely": 15, "max": 20}
        params = PERTParams.from_dict(data)
        assert params.min == 10
        assert params.likely == 15
        assert params.max == 20

    def test_to_dict(self):
        """Convert to dictionary."""
        params = PERTParams(min=10, likely=15, max=20)
        data = params.to_dict()
        assert data == {"min": 10, "likely": 15, "max": 20}


class TestAffordabilityParams:
    """Tests for AffordabilityParams."""

    def test_valid_params(self):
        """Valid affordability parameters."""
        params = AffordabilityParams(
            percentage_affordable=0.25,
            price_discount=0.15,
            restriction_years=30,
            legally_binding=True,
        )
        assert params.percentage_affordable == 0.25

    def test_invalid_percentage_over_1(self):
        """percentage > 1 should raise error."""
        with pytest.raises(ValueError):
            AffordabilityParams(
                percentage_affordable=1.5,
                price_discount=0.15,
                restriction_years=30,
                legally_binding=True,
            )

    def test_invalid_negative_years(self):
        """Negative restriction years should raise error."""
        with pytest.raises(ValueError):
            AffordabilityParams(
                percentage_affordable=0.25,
                price_discount=0.15,
                restriction_years=-5,
                legally_binding=True,
            )


class TestQualityParams:
    """Tests for QualityParams."""

    def test_valid_energy_ratings(self):
        """All valid energy ratings should work."""
        for rating in ["A+", "A", "B", "C", "D", "E", "F", "G"]:
            params = QualityParams(
                energy_rating=rating,
                defect_rate=PERTParams(min=0.01, likely=0.03, max=0.05),
            )
            assert params.energy_rating == rating

    def test_invalid_energy_rating(self):
        """Invalid energy rating should raise error."""
        with pytest.raises(ValueError):
            QualityParams(
                energy_rating="X",
                defect_rate=PERTParams(min=0.01, likely=0.03, max=0.05),
            )


class TestWeightProfile:
    """Tests for WeightProfile."""

    def test_weights_normalized(self):
        """Weights should be normalized to sum to 1."""
        profile = WeightProfile(
            id="test",
            name="Test",
            weights={"speed": 1, "affordability": 1, "quality": 1, "financial": 1},
        )
        total = sum(profile.weights.values())
        assert abs(total - 1.0) < 0.001

    def test_missing_objective_raises(self):
        """Missing required objective should raise error."""
        with pytest.raises(ValueError):
            WeightProfile(
                id="test",
                name="Test",
                weights={"speed": 0.25, "quality": 0.25, "financial": 0.25},
            )

    def test_negative_weight_raises(self):
        """Negative weight should raise error."""
        with pytest.raises(ValueError):
            WeightProfile(
                id="test",
                name="Test",
                weights={"speed": -0.1, "affordability": 0.4, "quality": 0.4, "financial": 0.3},
            )

    def test_create_custom(self):
        """Create custom weight profile."""
        profile = WeightProfile.create_custom(0.3, 0.3, 0.3, 0.1)
        assert profile.id == "custom"
        assert abs(profile.weights["speed"] - 0.3) < 0.001
        assert abs(profile.weights["financial"] - 0.1) < 0.001


class TestMarketScenario:
    """Tests for MarketScenario."""

    def test_valid_market(self):
        """Valid market scenario."""
        market = MarketScenario(
            id="M1",
            name="Test Market",
            description="Test",
            probability=0.5,
            parameters=MarketParams(
                construction_cost_multiplier=1.15,
                interest_rate=0.07,
                property_price_growth=0.01,
                sales_velocity_months=18,
                inflation_rate=0.04,
            ),
        )
        assert market.probability == 0.5

    def test_invalid_probability(self):
        """Probability > 1 should raise error."""
        with pytest.raises(ValueError):
            MarketScenario(
                id="M1",
                name="Test",
                description="Test",
                probability=1.5,
                parameters=MarketParams(
                    construction_cost_multiplier=1.15,
                    interest_rate=0.07,
                    property_price_growth=0.01,
                    sales_velocity_months=18,
                    inflation_rate=0.04,
                ),
            )
