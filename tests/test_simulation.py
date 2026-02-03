"""Tests for Monte Carlo simulation."""

import pytest
import numpy as np
from pathlib import Path

from hallar.models.scenario import (
    Scenario, PERTParams, RiskParams, AffordabilityParams,
    QualityParams, TimelineParams,
)
from hallar.models.market import MarketScenario, MarketParams
from hallar.models.constraints import ConstraintSet
from hallar.models.weights import WeightProfile
from hallar.simulation.monte_carlo import (
    MonteCarloSimulation,
    run_simulation,
    run_full_analysis,
)
from hallar.io.loaders import load_scenarios, load_markets, load_constraints


def create_test_scenario() -> Scenario:
    """Create a test scenario for unit tests."""
    return Scenario(
        id="TEST",
        name="Test Scenario",
        description="A test scenario for unit testing",
        infrastructure_cost=PERTParams(min=8000, likely=10000, max=15000),
        rights_revenue=PERTParams(min=12000, likely=15000, max=18000),
        timeline=TimelineParams(
            first_units=PERTParams(min=30, likely=40, max=60),
            first_school=PERTParams(min=40, likely=50, max=70),
            sixty_percent_complete=PERTParams(min=60, likely=80, max=120),
        ),
        risks=RiskParams(
            cost_overrun_probability=0.4,
            cost_overrun_multiplier=PERTParams(min=1.0, likely=1.1, max=1.3),
            developer_default_probability=0.05,
            delay_probability=0.3,
            delay_months=PERTParams(min=0, likely=5, max=15),
        ),
        affordability=AffordabilityParams(
            percentage_affordable=0.25,
            price_discount=0.15,
            restriction_years=30,
            legally_binding=True,
        ),
        quality=QualityParams(
            energy_rating="A",
            defect_rate=PERTParams(min=0.01, likely=0.03, max=0.07),
        ),
        city_control=0.7,
        step_in_cost_fraction=0.25,
    )


def create_test_market() -> MarketScenario:
    """Create a test market scenario."""
    return MarketScenario(
        id="M_TEST",
        name="Test Market",
        description="Test market conditions",
        probability=1.0,
        parameters=MarketParams(
            construction_cost_multiplier=1.15,
            interest_rate=0.07,
            property_price_growth=0.01,
            sales_velocity_months=18,
            inflation_rate=0.04,
            developer_default_multiplier=1.0,
        ),
    )


class TestMonteCarloSimulation:
    """Tests for Monte Carlo simulation engine."""

    def test_simulation_runs(self):
        """Smoke test: simulation completes without error."""
        scenario = create_test_scenario()
        market = create_test_market()

        results = run_simulation(scenario, market, n_simulations=100, random_seed=42)

        assert len(results.npv) == 100
        assert len(results.first_units_months) == 100
        assert len(results.sixty_percent_months) == 100

    def test_simulation_reproducibility(self):
        """Same seed should produce same results."""
        scenario = create_test_scenario()
        market = create_test_market()

        results1 = run_simulation(scenario, market, n_simulations=100, random_seed=42)
        results2 = run_simulation(scenario, market, n_simulations=100, random_seed=42)

        np.testing.assert_array_equal(results1.npv, results2.npv)

    def test_simulation_different_seeds(self):
        """Different seeds should produce different results."""
        scenario = create_test_scenario()
        market = create_test_market()

        results1 = run_simulation(scenario, market, n_simulations=100, random_seed=42)
        results2 = run_simulation(scenario, market, n_simulations=100, random_seed=123)

        assert not np.array_equal(results1.npv, results2.npv)

    def test_npv_reasonable_range(self):
        """NPV should be in reasonable range based on inputs."""
        scenario = create_test_scenario()
        market = create_test_market()

        results = run_simulation(scenario, market, n_simulations=1000, random_seed=42)

        # Revenue minus cost should give rough NPV range
        # Revenue: 12k-18k, Cost: 8k-15k * 1.15 = 9.2k-17.25k
        # NPV should roughly be in -10k to +15k range (accounting for discounting)
        assert results.npv.min() > -20000
        assert results.npv.max() < 30000

    def test_timeline_within_bounds(self):
        """Timeline results should be within PERT bounds (with delays)."""
        scenario = create_test_scenario()
        market = create_test_market()

        results = run_simulation(scenario, market, n_simulations=1000, random_seed=42)

        # First units: 30-60 months base, plus potential delays (0-15)
        assert results.first_units_months.min() >= 30
        assert results.first_units_months.max() <= 60 + 15 + 18  # Max delay + default delay

    def test_quality_score_range(self):
        """Quality scores should be in valid range."""
        scenario = create_test_scenario()
        market = create_test_market()

        results = run_simulation(scenario, market, n_simulations=1000, random_seed=42)

        assert results.quality_score.min() >= 0
        assert results.quality_score.max() <= 100

    def test_affordability_score_consistent(self):
        """Affordability score should be deterministic (not random)."""
        scenario = create_test_scenario()
        market = create_test_market()

        results = run_simulation(scenario, market, n_simulations=100, random_seed=42)

        # All values should be the same (affordability is deterministic)
        unique_values = np.unique(results.affordability_score)
        assert len(unique_values) == 1

    def test_developer_default_happens(self):
        """With non-zero default probability, some defaults should occur."""
        scenario = create_test_scenario()
        market = create_test_market()

        results = run_simulation(scenario, market, n_simulations=1000, random_seed=42)

        # With 5% default probability, we should see some defaults
        default_rate = np.mean(results.developer_defaulted)
        assert default_rate > 0.01  # At least 1%
        assert default_rate < 0.20  # Less than 20%


class TestFullAnalysis:
    """Tests for full analysis pipeline."""

    def test_full_analysis_runs(self):
        """Full analysis completes without error."""
        scenario = create_test_scenario()
        market = create_test_market()

        constraints = ConstraintSet()  # Empty constraints
        weights = WeightProfile.create_custom(0.25, 0.25, 0.25, 0.25)

        results = run_full_analysis(
            scenarios=[scenario],
            markets=[market],
            constraints=constraints,
            weights=weights,
            n_simulations=100,
            random_seed=42,
        )

        assert len(results.scenario_results) == 1
        assert len(results.ranked_results) == 1

    def test_full_analysis_ranking(self):
        """Scenarios should be ranked by utility."""
        scenario1 = create_test_scenario()
        scenario2 = create_test_scenario()
        scenario2.id = "TEST2"
        scenario2.name = "Test Scenario 2"
        # Make scenario2 worse
        scenario2.infrastructure_cost = PERTParams(min=15000, likely=20000, max=25000)

        market = create_test_market()
        constraints = ConstraintSet()
        weights = WeightProfile.create_custom(0.25, 0.25, 0.25, 0.25)

        results = run_full_analysis(
            scenarios=[scenario1, scenario2],
            markets=[market],
            constraints=constraints,
            weights=weights,
            n_simulations=100,
            random_seed=42,
        )

        # Both should be ranked
        assert len(results.ranked_results) == 2
        # Should be sorted by utility (descending)
        assert results.ranked_results[0].utility >= results.ranked_results[1].utility

    def test_utility_in_valid_range(self):
        """Utility scores should be between 0 and 1."""
        scenario = create_test_scenario()
        market = create_test_market()
        constraints = ConstraintSet()
        weights = WeightProfile.create_custom(0.25, 0.25, 0.25, 0.25)

        results = run_full_analysis(
            scenarios=[scenario],
            markets=[market],
            constraints=constraints,
            weights=weights,
            n_simulations=100,
            random_seed=42,
        )

        for result in results.scenario_results:
            assert 0 <= result.utility <= 1

    def test_metrics_calculated(self):
        """All expected metrics should be calculated."""
        scenario = create_test_scenario()
        market = create_test_market()
        constraints = ConstraintSet()
        weights = WeightProfile.create_custom(0.25, 0.25, 0.25, 0.25)

        results = run_full_analysis(
            scenarios=[scenario],
            markets=[market],
            constraints=constraints,
            weights=weights,
            n_simulations=100,
            random_seed=42,
        )

        metrics = results.scenario_results[0].metrics
        required_metrics = [
            "expected_npv", "npv_std", "npv_p10", "npv_p90",
            "cvar_05", "prob_loss", "expected_time", "quality_score",
            "affordability_score",
        ]

        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"


class TestWithExampleData:
    """Integration tests using example data files."""

    @pytest.fixture
    def example_data_dir(self):
        """Path to example data directory."""
        return Path(__file__).parent.parent / "data" / "examples"

    def test_load_and_run_example_data(self, example_data_dir):
        """Full integration test with example data."""
        if not example_data_dir.exists():
            pytest.skip("Example data not found")

        scenarios = load_scenarios(example_data_dir / "scenarios_example.yaml")
        markets = load_markets(example_data_dir / "market_scenarios.yaml")
        constraints = load_constraints(example_data_dir / "constraints.yaml")
        weights = WeightProfile.create_custom(0.25, 0.25, 0.25, 0.25)

        assert len(scenarios) > 0
        assert len(markets) > 0

        results = run_full_analysis(
            scenarios=scenarios,
            markets=markets,
            constraints=constraints,
            weights=weights,
            n_simulations=100,
            random_seed=42,
        )

        assert len(results.scenario_results) == len(scenarios)
        # At least some scenarios should pass constraints
        # (depending on constraint settings)
