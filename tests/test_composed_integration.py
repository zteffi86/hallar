"""Integration tests for ComposedScenario and extended SimulationResults."""

import pytest
import numpy as np
import yaml
from pathlib import Path

from hallar.models import (
    ComposedScenario,
    ComposedScenarioSet,
    GoalSet,
    OwnershipSet,
    FinancingSet,
    ByggingarretturSet,
    InfrastructureSet,
    CounterpartySet,
    HallarParameters,
    GoalScores,
    ScenarioComponents,
)
from hallar.simulation.monte_carlo import SimulationResults
from hallar.simulation.composed_runner import (
    ComposedScenarioRunner,
    ComponentRegistry,
    ComposedSimulationConfig,
    run_composed_analysis,
    compute_goal_metrics,
    rank_scenarios_by_utility,
)
from hallar.analysis.goal_mapping import (
    compute_goal_metrics_from_simulation,
    analyze_scenario_goals,
)


DATA_DIR = Path(__file__).parent.parent / "data"


def load_yaml(path: Path):
    """Load YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def create_test_simulation_results(n: int = 1000) -> SimulationResults:
    """Create test simulation results with all fields populated."""
    rng = np.random.default_rng(42)

    return SimulationResults(
        npv=rng.normal(5000, 2000, n),
        first_units_months=rng.normal(36, 6, n),
        first_school_months=rng.normal(48, 8, n),
        sixty_percent_months=rng.normal(60, 10, n),
        total_cost=rng.normal(15000, 3000, n),
        total_revenue=rng.normal(20000, 4000, n),
        quality_score=rng.uniform(60, 95, n),
        affordability_score=rng.uniform(40, 80, n),
        developer_defaulted=rng.random(n) < 0.05,
        # Extended fields
        affordable_percentage=np.full(n, 0.30),
        defect_rate=rng.beta(2, 50, n),
        city_control=np.full(n, 0.75),
        risk_score=rng.uniform(60, 90, n),
        control_score=np.full(n, 75.0),
    )


def create_test_composed_scenario() -> ComposedScenario:
    """Create a test ComposedScenario for unit tests."""
    from hallar.models.scenario import PERTParams

    return ComposedScenario(
        id="TEST_COMPOSED",
        name="Test Composed Scenario",
        name_is="Prófunarsviðsmynd",
        description="A test scenario for integration testing",
        counterparty="C_DEVELOPER_A",
        components=ScenarioComponents(
            ownership="O1",
            financing="F1",
            byggingarrettur="B1",
            infrastructure="I1",
        ),
        goal_scores=GoalScores(
            speed=70,
            affordability=65,
            quality=75,
            financial=60,
            risk=70,
            control=80,
        ),
        city_control_score=75,
        default_probability=PERTParams(min=0.02, likely=0.05, max=0.12),
    )


class TestSimulationResultsExtended:
    """Tests for extended SimulationResults fields and properties."""

    def test_new_fields_exist(self):
        """SimulationResults should have all new fields."""
        results = create_test_simulation_results(100)

        # Check new fields exist
        assert hasattr(results, 'affordable_percentage')
        assert hasattr(results, 'defect_rate')
        assert hasattr(results, 'city_control')
        assert hasattr(results, 'risk_score')
        assert hasattr(results, 'control_score')

    def test_new_fields_have_correct_shape(self):
        """New fields should have correct array shapes."""
        n = 500
        results = create_test_simulation_results(n)

        assert len(results.affordable_percentage) == n
        assert len(results.defect_rate) == n
        assert len(results.city_control) == n
        assert len(results.risk_score) == n
        assert len(results.control_score) == n

    def test_computed_properties_exist(self):
        """SimulationResults should have all computed properties."""
        results = create_test_simulation_results(100)

        # Check properties exist and return values
        assert isinstance(results.prob_negative, float)
        assert isinstance(results.prob_loss, float)
        assert isinstance(results.cvar_05, float)
        assert isinstance(results.expected_npv, float)
        assert isinstance(results.npv_std, float)
        assert isinstance(results.expected_time, float)

    def test_prob_negative_calculation(self):
        """prob_negative should correctly calculate probability of negative NPV."""
        rng = np.random.default_rng(42)
        n = 1000

        # Create results with known negative probability
        npv = np.concatenate([
            np.full(300, -1000),  # 30% negative
            np.full(700, 5000),   # 70% positive
        ])
        rng.shuffle(npv)

        results = SimulationResults(
            npv=npv,
            first_units_months=np.zeros(n),
            first_school_months=np.zeros(n),
            sixty_percent_months=np.zeros(n),
            total_cost=np.zeros(n),
            total_revenue=np.zeros(n),
            quality_score=np.zeros(n),
            affordability_score=np.zeros(n),
            developer_defaulted=np.zeros(n, dtype=bool),
        )

        assert abs(results.prob_negative - 0.30) < 0.01

    def test_prob_loss_is_alias(self):
        """prob_loss should be alias for prob_negative."""
        results = create_test_simulation_results(100)
        assert results.prob_loss == results.prob_negative

    def test_cvar_05_calculation(self):
        """cvar_05 should calculate conditional value at risk at 5% level."""
        results = create_test_simulation_results(1000)

        # CVaR should be less than or equal to the 5th percentile
        p5 = np.percentile(results.npv, 5)
        assert results.cvar_05 <= p5

    def test_expected_npv_calculation(self):
        """expected_npv should be mean of NPV array."""
        results = create_test_simulation_results(1000)
        assert abs(results.expected_npv - np.mean(results.npv)) < 0.01

    def test_to_dict_includes_new_fields(self):
        """to_dict should include new fields."""
        results = create_test_simulation_results(100)
        d = results.to_dict()

        assert 'affordable_percentage' in d
        assert 'city_control' in d
        assert 'risk_score' in d
        assert 'cvar_05' in d
        assert 'prob_loss' in d

    def test_default_empty_arrays(self):
        """New fields should default to empty arrays."""
        results = SimulationResults(
            npv=np.array([1000, 2000, 3000]),
            first_units_months=np.array([30, 35, 40]),
            first_school_months=np.array([40, 45, 50]),
            sixty_percent_months=np.array([60, 65, 70]),
            total_cost=np.array([10000, 11000, 12000]),
            total_revenue=np.array([15000, 16000, 17000]),
            quality_score=np.array([80, 85, 90]),
            affordability_score=np.array([60, 65, 70]),
            developer_defaulted=np.array([False, False, True]),
        )

        # Extended fields should default to empty arrays
        assert len(results.affordable_percentage) == 0
        assert len(results.defect_rate) == 0
        assert len(results.city_control) == 0


class TestComposedScenarioRunner:
    """Tests for ComposedScenarioRunner."""

    @pytest.fixture
    def registry(self):
        """Create a ComponentRegistry from data files."""
        if not DATA_DIR.exists():
            pytest.skip("Data directory not found")

        return ComponentRegistry(
            ownership=OwnershipSet.from_dict(load_yaml(DATA_DIR / "ownership_structures.yaml")),
            financing=FinancingSet.from_dict(load_yaml(DATA_DIR / "financing_models.yaml")),
            byggingarrettur=ByggingarretturSet.from_dict(load_yaml(DATA_DIR / "byggingarrettur_options.yaml")),
            infrastructure=InfrastructureSet.from_dict(load_yaml(DATA_DIR / "infrastructure_models.yaml")),
            counterparties=CounterpartySet.from_dict(load_yaml(DATA_DIR / "counterparty_profiles.yaml")),
            hallar_params=HallarParameters.from_dict(load_yaml(DATA_DIR / "hallar_parameters.yaml")),
        )

    def test_runner_creates_results(self, registry):
        """ComposedScenarioRunner should create valid SimulationResults."""
        config = ComposedSimulationConfig(
            n_simulations=100,
            random_seed=42,
        )
        runner = ComposedScenarioRunner(registry, config)
        scenario = create_test_composed_scenario()

        results = runner.run_scenario(scenario)

        assert isinstance(results, SimulationResults)
        assert len(results.npv) == 100
        assert len(results.first_units_months) == 100

    def test_runner_populates_extended_fields(self, registry):
        """ComposedScenarioRunner should populate all extended fields."""
        config = ComposedSimulationConfig(
            n_simulations=100,
            random_seed=42,
        )
        runner = ComposedScenarioRunner(registry, config)
        scenario = create_test_composed_scenario()

        results = runner.run_scenario(scenario)

        # Check extended fields are populated
        assert len(results.affordable_percentage) == 100
        assert len(results.defect_rate) == 100
        assert len(results.city_control) == 100
        assert len(results.risk_score) == 100
        assert len(results.control_score) == 100

    def test_runner_respects_affordability_pct(self, registry):
        """ComposedScenarioRunner should respect affordability percentage."""
        config = ComposedSimulationConfig(
            n_simulations=100,
            random_seed=42,
            affordability_slider=0.40,
        )
        runner = ComposedScenarioRunner(registry, config)
        scenario = create_test_composed_scenario()

        results = runner.run_scenario(scenario, affordability_pct=0.50)

        # Should use override value
        assert np.all(results.affordable_percentage == 0.50)

    def test_runner_reproducibility(self, registry):
        """Same seed should produce same results."""
        scenario = create_test_composed_scenario()

        config1 = ComposedSimulationConfig(n_simulations=100, random_seed=42)
        runner1 = ComposedScenarioRunner(registry, config1)
        results1 = runner1.run_scenario(scenario)

        config2 = ComposedSimulationConfig(n_simulations=100, random_seed=42)
        runner2 = ComposedScenarioRunner(registry, config2)
        results2 = runner2.run_scenario(scenario)

        np.testing.assert_array_almost_equal(results1.npv, results2.npv)

    def test_run_all_scenarios(self, registry):
        """run_all_scenarios should process multiple scenarios."""
        if not (DATA_DIR / "composed_scenarios.yaml").exists():
            pytest.skip("Composed scenarios file not found")

        scenarios = ComposedScenarioSet.from_dict(load_yaml(DATA_DIR / "composed_scenarios.yaml"))
        config = ComposedSimulationConfig(n_simulations=50, random_seed=42)
        runner = ComposedScenarioRunner(registry, config)

        results = runner.run_all_scenarios(scenarios)

        assert len(results) == len(scenarios.scenarios)
        for scenario_id in scenarios.scenarios:
            assert scenario_id in results
            assert isinstance(results[scenario_id], SimulationResults)


class TestGoalMappingWithExtendedFields:
    """Tests for goal_mapping with extended SimulationResults."""

    def test_compute_goal_metrics_from_simulation(self):
        """Goal metrics should be computed from simulation results."""
        results = create_test_simulation_results(1000)

        # Test each goal
        for goal_id, direction in [
            ("G1", "minimize"),  # Speed - lower is better
            ("G2", "maximize"),  # Affordability
            ("G3", "maximize"),  # Quality
            ("G4", "maximize"),  # Financial
            ("G5", "minimize"),  # Risk - lower is better
            ("G6", "maximize"),  # Control
        ]:
            raw_value, normalized = compute_goal_metrics_from_simulation(
                results, goal_id, direction
            )

            assert isinstance(raw_value, float)
            assert isinstance(normalized, float)
            assert 0 <= normalized <= 100

    def test_goal_metrics_use_extended_fields(self):
        """Goal metrics should use extended fields when available."""
        n = 1000
        results = create_test_simulation_results(n)

        # G2 (Affordability) should use affordable_percentage
        raw_g2, _ = compute_goal_metrics_from_simulation(results, "G2", "maximize")
        expected_g2 = float(np.mean(results.affordable_percentage)) * 100
        assert abs(raw_g2 - expected_g2) < 1.0

        # G6 (Control) should use city_control
        raw_g6, _ = compute_goal_metrics_from_simulation(results, "G6", "maximize")
        expected_g6 = float(np.mean(results.city_control)) * 100
        assert abs(raw_g6 - expected_g6) < 1.0

    def test_fallback_to_original_fields(self):
        """Should fall back to original fields when extended fields are empty."""
        n = 100
        results = SimulationResults(
            npv=np.random.normal(5000, 2000, n),
            first_units_months=np.random.normal(36, 6, n),
            first_school_months=np.random.normal(48, 8, n),
            sixty_percent_months=np.random.normal(60, 10, n),
            total_cost=np.random.normal(15000, 3000, n),
            total_revenue=np.random.normal(20000, 4000, n),
            quality_score=np.full(n, 75.0),
            affordability_score=np.full(n, 60.0),
            developer_defaulted=np.zeros(n, dtype=bool),
            # Leave extended fields as defaults (empty arrays)
        )

        # G2 should fall back to affordability_score
        raw_g2, _ = compute_goal_metrics_from_simulation(results, "G2", "maximize")
        assert abs(raw_g2 - 60.0) < 1.0

        # G3 should fall back to quality_score
        raw_g3, _ = compute_goal_metrics_from_simulation(results, "G3", "maximize")
        assert abs(raw_g3 - 75.0) < 1.0


class TestRunComposedAnalysis:
    """Tests for run_composed_analysis function."""

    @pytest.fixture
    def registry(self):
        """Create a ComponentRegistry from data files."""
        if not DATA_DIR.exists():
            pytest.skip("Data directory not found")

        return ComponentRegistry(
            ownership=OwnershipSet.from_dict(load_yaml(DATA_DIR / "ownership_structures.yaml")),
            financing=FinancingSet.from_dict(load_yaml(DATA_DIR / "financing_models.yaml")),
            byggingarrettur=ByggingarretturSet.from_dict(load_yaml(DATA_DIR / "byggingarrettur_options.yaml")),
            infrastructure=InfrastructureSet.from_dict(load_yaml(DATA_DIR / "infrastructure_models.yaml")),
            counterparties=CounterpartySet.from_dict(load_yaml(DATA_DIR / "counterparty_profiles.yaml")),
            hallar_params=HallarParameters.from_dict(load_yaml(DATA_DIR / "hallar_parameters.yaml")),
        )

    def test_run_composed_analysis(self, registry):
        """run_composed_analysis should complete successfully."""
        if not DATA_DIR.exists():
            pytest.skip("Data directory not found")

        scenarios = ComposedScenarioSet.from_dict(load_yaml(DATA_DIR / "composed_scenarios.yaml"))
        goals = GoalSet.from_dict(load_yaml(DATA_DIR / "goals.yaml"))

        results = run_composed_analysis(
            scenarios=scenarios,
            registry=registry,
            goals=goals,
            weight_preset="balanced",
            n_simulations=50,
            random_seed=42,
            affordability_pct=0.30,
        )

        assert 'simulation_results' in results
        assert 'rankings' in results
        assert 'weights' in results
        assert len(results['simulation_results']) == len(scenarios.scenarios)
        assert len(results['rankings']) == len(scenarios.scenarios)

    def test_rankings_sorted_by_utility(self, registry):
        """Rankings should be sorted by utility (highest first)."""
        if not DATA_DIR.exists():
            pytest.skip("Data directory not found")

        scenarios = ComposedScenarioSet.from_dict(load_yaml(DATA_DIR / "composed_scenarios.yaml"))
        goals = GoalSet.from_dict(load_yaml(DATA_DIR / "goals.yaml"))

        results = run_composed_analysis(
            scenarios=scenarios,
            registry=registry,
            goals=goals,
            n_simulations=50,
            random_seed=42,
        )

        rankings = results['rankings']
        for i in range(len(rankings) - 1):
            assert rankings[i].total_utility >= rankings[i + 1].total_utility

    def test_different_weight_presets(self, registry):
        """Different weight presets should produce different rankings."""
        if not DATA_DIR.exists():
            pytest.skip("Data directory not found")

        scenarios = ComposedScenarioSet.from_dict(load_yaml(DATA_DIR / "composed_scenarios.yaml"))
        goals = GoalSet.from_dict(load_yaml(DATA_DIR / "goals.yaml"))

        # Run with two different presets
        results_balanced = run_composed_analysis(
            scenarios=scenarios,
            registry=registry,
            goals=goals,
            weight_preset="balanced",
            n_simulations=50,
            random_seed=42,
        )

        results_speed = run_composed_analysis(
            scenarios=scenarios,
            registry=registry,
            goals=goals,
            weight_preset="speed_focused",
            n_simulations=50,
            random_seed=42,
        )

        # Different weights should produce different utility values
        balanced_utilities = [r.total_utility for r in results_balanced['rankings']]
        speed_utilities = [r.total_utility for r in results_speed['rankings']]

        # At least some utilities should differ
        assert balanced_utilities != speed_utilities
