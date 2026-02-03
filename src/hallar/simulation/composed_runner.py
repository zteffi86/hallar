"""Monte Carlo runner for ComposedScenario models."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np

from hallar.models import (
    ComposedScenario,
    ComposedScenarioSet,
    OwnershipSet,
    FinancingSet,
    ByggingarretturSet,
    InfrastructureSet,
    CounterpartySet,
    HallarParameters,
    GoalSet,
)
from hallar.simulation.distributions import pert_distribution
from hallar.simulation.monte_carlo import SimulationResults


@dataclass
class ComponentRegistry:
    """Registry of all component sets for lookup."""

    ownership: OwnershipSet
    financing: FinancingSet
    byggingarrettur: ByggingarretturSet
    infrastructure: InfrastructureSet
    counterparties: CounterpartySet
    hallar_params: HallarParameters


@dataclass
class ComposedSimulationConfig:
    """Configuration for composed scenario simulation."""

    n_simulations: int = 10000
    random_seed: Optional[int] = 42
    discount_rate: float = 0.05
    affordability_slider: float = 0.30  # 0-1, default 30% affordable


class ComposedScenarioRunner:
    """Run Monte Carlo simulations for ComposedScenario models."""

    def __init__(
        self,
        registry: ComponentRegistry,
        config: ComposedSimulationConfig,
    ):
        self.registry = registry
        self.config = config
        self.rng = np.random.default_rng(config.random_seed)

    def run_scenario(
        self,
        scenario: ComposedScenario,
        affordability_pct: Optional[float] = None,
    ) -> SimulationResults:
        """Run Monte Carlo simulation for a single composed scenario.

        Args:
            scenario: ComposedScenario to simulate
            affordability_pct: Override affordability percentage (0-1)

        Returns:
            SimulationResults with all fields populated
        """
        n = self.config.n_simulations
        params = self.registry.hallar_params

        # Get affordability setting
        afford_pct = affordability_pct or self.config.affordability_slider
        if scenario.affordability_commitment:
            afford_pct = max(afford_pct, scenario.affordability_commitment.minimum_pct)

        # Resolve counterparty profile
        counterparty = self.registry.counterparties.get(scenario.counterparty)

        # Sample default probability from counterparty profile
        if counterparty:
            default_probs = pert_distribution(
                counterparty.default_probability.min,
                counterparty.default_probability.likely,
                counterparty.default_probability.max,
                n,
                self.rng,
            )
        else:
            default_probs = np.full(n, scenario.get_default_probability_likely())

        # Determine if default occurs
        developer_defaulted = self.rng.random(n) < default_probs

        # Resolve byggingarrétt option for NPV calculation
        bygg_id = scenario.components.byggingarrettur
        bygg_option = (
            self.registry.byggingarrettur.options.get(bygg_id)
            if bygg_id != "N/A"
            else None
        )

        # Resolve infrastructure model
        infra_id = scenario.components.infrastructure
        infra_model = self.registry.infrastructure.models.get(infra_id)

        # Calculate NPV based on structure
        npv, total_cost, total_revenue = self._calculate_npv(
            scenario,
            bygg_option,
            infra_model,
            counterparty,
            afford_pct,
            developer_defaulted,
            n,
        )

        # Sample timeline
        first_units_months = self._sample_timeline(scenario, developer_defaulted, n)
        sixty_percent_months = first_units_months + self.rng.normal(24, 6, n)
        sixty_percent_months = np.maximum(sixty_percent_months, first_units_months + 6)

        # First school - tied to infrastructure completion
        first_school_months = first_units_months + self.rng.normal(12, 3, n)
        first_school_months = np.maximum(first_school_months, first_units_months)

        # Quality metrics
        base_defect_rate = 0.03  # 3% baseline
        if scenario.goal_scores.quality >= 80:
            base_defect_rate = 0.01
        elif scenario.goal_scores.quality >= 60:
            base_defect_rate = 0.02
        elif scenario.goal_scores.quality <= 40:
            base_defect_rate = 0.05

        defect_rate = self.rng.beta(2, 50, n) + base_defect_rate * 0.5
        quality_score = 100 - defect_rate * 1000  # Convert to 0-100 scale
        quality_score = np.clip(quality_score, 0, 100)

        # Affordability metrics
        affordable_percentage = np.full(n, afford_pct)
        affordability_score = np.full(n, float(scenario.goal_scores.affordability))

        # City control (constant for scenario)
        city_control = np.full(n, scenario.city_control_score / 100.0)

        # Risk score (inverse of default probability, scaled)
        risk_score = 100 - default_probs * 500  # 20% default = 0 risk score
        risk_score = np.clip(risk_score, 0, 100)

        # Control score (same as city_control but 0-100)
        control_score = np.full(n, float(scenario.city_control_score))

        return SimulationResults(
            npv=npv,
            first_units_months=first_units_months,
            first_school_months=first_school_months,
            sixty_percent_months=sixty_percent_months,
            total_cost=total_cost,
            total_revenue=total_revenue,
            quality_score=quality_score,
            affordability_score=affordability_score,
            developer_defaulted=developer_defaulted,
            affordable_percentage=affordable_percentage,
            defect_rate=defect_rate,
            city_control=city_control,
            risk_score=risk_score,
            control_score=control_score,
        )

    def _calculate_npv(
        self,
        scenario: ComposedScenario,
        bygg_option: Optional[Any],
        infra_model: Optional[Any],
        counterparty: Optional[Any],
        afford_pct: float,
        developer_defaulted: np.ndarray,
        n: int,
    ) -> tuple:
        """Calculate NPV based on scenario structure.

        Returns:
            Tuple of (npv, total_cost, total_revenue)
        """
        params = self.registry.hallar_params

        # Base values from hallar_params
        bygg_value = pert_distribution(
            params.byggingarrettur_valuation.total_value.min,
            params.byggingarrettur_valuation.total_value.likely,
            params.byggingarrettur_valuation.total_value.max,
            n,
            self.rng,
        )

        infra_cost = pert_distribution(
            params.infrastructure_costs.total.min,
            params.infrastructure_costs.total.likely,
            params.infrastructure_costs.total.max,
            n,
            self.rng,
        )

        # Affordability impact on revenue
        # Revenue reduction = affordable_pct × depth (assume 30% below market)
        affordability_depth = 0.30
        revenue_multiplier = 1 - (afford_pct * affordability_depth)

        # Calculate NPV by byggingarrétt type
        if bygg_option is None or bygg_option.id in ["B1", "B2"]:
            # Sale scenarios: City receives cash, pays infrastructure
            if bygg_option and bygg_option.id == "B2":
                # Discounted sale
                bygg_value = bygg_value * 0.85
            npv = bygg_value * revenue_multiplier - infra_cost
            total_revenue = bygg_value * revenue_multiplier
            total_cost = infra_cost.copy()

        elif bygg_option.id == "B3":
            # Equity/JV: City receives share of project profits
            city_share = scenario.city_control_score / 100.0
            project_profit = bygg_value * 1.2 - infra_cost  # Assume 20% development margin
            npv = project_profit * city_share * revenue_multiplier
            total_revenue = project_profit * city_share * revenue_multiplier + infra_cost
            total_cost = infra_cost.copy()

        elif bygg_option.id == "B4":
            # Annual lease: City receives annual payments
            annual_payment = bygg_value * 0.05  # 5% annual return
            years = 30
            discount = self.config.discount_rate
            pv_factor = (1 - (1 + discount) ** -years) / discount
            npv = annual_payment * pv_factor * revenue_multiplier - infra_cost
            total_revenue = annual_payment * pv_factor * revenue_multiplier
            total_cost = infra_cost.copy()

        elif bygg_option.id == "B5":
            # Infrastructure swap: Net zero (byggingarrétt = infra)
            npv = np.zeros(n)  # NPV neutral by design
            total_revenue = bygg_value.copy()
            total_cost = bygg_value.copy()

        elif bygg_option.id == "B6":
            # Hybrid: 50% sale + 50% equity
            sale_portion = bygg_value * 0.5 * revenue_multiplier
            equity_portion = (
                (bygg_value * 0.5 * 1.2 - infra_cost * 0.5) * 0.5 * revenue_multiplier
            )
            npv = sale_portion + equity_portion - infra_cost * 0.5
            total_revenue = sale_portion + equity_portion + infra_cost * 0.5
            total_cost = infra_cost.copy()

        else:
            # Default calculation
            npv = bygg_value * revenue_multiplier - infra_cost
            total_revenue = bygg_value * revenue_multiplier
            total_cost = infra_cost.copy()

        # Apply infrastructure model adjustments
        if infra_model:
            if infra_model.id == "I2":
                # Developer builds: City saves on infra but loses some control
                npv = npv + infra_cost * 0.8  # City doesn't pay infra directly
            elif infra_model.id in ["I5", "I6"]:
                # Swap or pension-financed: Reduced city outlay
                npv = npv + infra_cost * 0.9

        # Apply cost overrun risk
        cost_overrun_prob = 0.4
        cost_overrun_pct = pert_distribution(0, 0.15, 0.50, n, self.rng)
        has_overrun = self.rng.random(n) < cost_overrun_prob
        npv = np.where(has_overrun, npv - infra_cost * cost_overrun_pct, npv)
        total_cost = np.where(
            has_overrun, total_cost + infra_cost * cost_overrun_pct, total_cost
        )

        # Apply default impact
        recovery_rate = 0.5
        if counterparty:
            recovery_rate = counterparty.recovery_rate
        npv = np.where(developer_defaulted, npv * recovery_rate, npv)

        return npv, total_cost, total_revenue

    def _sample_timeline(
        self,
        scenario: ComposedScenario,
        developer_defaulted: np.ndarray,
        n: int,
    ) -> np.ndarray:
        """Sample timeline to first units."""
        # Base timeline from goal score (higher speed score = faster)
        speed_score = scenario.goal_scores.speed

        # Convert speed score to months (100 = 24 months, 0 = 60 months)
        base_months = 60 - (speed_score / 100) * 36

        # Sample with uncertainty
        months = self.rng.normal(base_months, 6, n)
        months = np.maximum(months, 18)  # Minimum 18 months

        # Delay if default
        delay_months = self.rng.exponential(12, n)
        months = np.where(developer_defaulted, months + delay_months, months)

        return months

    def run_all_scenarios(
        self,
        scenarios: ComposedScenarioSet,
        affordability_pct: Optional[float] = None,
    ) -> Dict[str, SimulationResults]:
        """Run simulation for all scenarios.

        Returns:
            Dict mapping scenario_id to SimulationResults
        """
        results = {}
        for scenario_id, scenario in scenarios.scenarios.items():
            results[scenario_id] = self.run_scenario(scenario, affordability_pct)
        return results


@dataclass
class GoalMetricResult:
    """Result of computing a goal metric."""

    goal_id: str
    raw_value: float
    normalized_score: float
    weight: float
    weighted_contribution: float


@dataclass
class ScenarioGoalAnalysis:
    """Complete goal analysis for a scenario."""

    scenario_id: str
    metrics: Dict[str, GoalMetricResult]
    total_utility: float


def compute_goal_metrics(
    scenario: ComposedScenario,
    results: SimulationResults,
    goals: GoalSet,
    weights: Dict[str, float],
) -> ScenarioGoalAnalysis:
    """Compute goal metrics from simulation results.

    Args:
        scenario: The scenario being analyzed
        results: Simulation results
        goals: Goal definitions
        weights: Weight dictionary (goal_id -> weight)

    Returns:
        ScenarioGoalAnalysis with all goal metrics
    """
    metrics = {}
    total_utility = 0.0

    for goal_id, goal in goals.goals.items():
        weight = weights.get(goal_id, 0.0)

        # Compute raw value based on goal type
        if goal_id == "G1":  # Speed
            raw_value = float(np.mean(results.first_units_months))
            normalized = max(0, min(100, (60 - raw_value) / 36 * 100))
        elif goal_id == "G2":  # Affordability
            raw_value = float(np.mean(results.affordable_percentage)) * 100
            normalized = raw_value
        elif goal_id == "G3":  # Quality
            raw_value = float(np.mean(results.quality_score))
            normalized = raw_value
        elif goal_id == "G4":  # Financial
            raw_value = float(np.mean(results.npv))
            # Normalize: -2000 = 0, 10000 = 100
            normalized = max(0, min(100, (raw_value + 2000) / 12000 * 100))
        elif goal_id == "G5":  # Risk
            raw_value = results.prob_loss * 100
            # Lower prob = higher score
            normalized = max(0, min(100, 100 - raw_value * 2))
        elif goal_id == "G6":  # Control
            raw_value = float(np.mean(results.city_control)) * 100
            normalized = raw_value
        else:
            raw_value = 50.0
            normalized = 50.0

        weighted_contribution = normalized * weight

        metrics[goal_id] = GoalMetricResult(
            goal_id=goal_id,
            raw_value=raw_value,
            normalized_score=normalized,
            weight=weight,
            weighted_contribution=weighted_contribution,
        )

        total_utility += weighted_contribution

    return ScenarioGoalAnalysis(
        scenario_id=scenario.id,
        metrics=metrics,
        total_utility=total_utility,
    )


def rank_scenarios_by_utility(
    scenarios: ComposedScenarioSet,
    goals: GoalSet,
    weights: Dict[str, float],
    simulation_results: Dict[str, SimulationResults],
) -> List[ScenarioGoalAnalysis]:
    """Rank scenarios by weighted utility.

    Args:
        scenarios: All scenarios
        goals: Goal definitions
        weights: Weight dictionary
        simulation_results: Simulation results by scenario ID

    Returns:
        List of ScenarioGoalAnalysis sorted by utility (highest first)
    """
    analyses = []

    for scenario_id, scenario in scenarios.scenarios.items():
        if scenario_id in simulation_results:
            analysis = compute_goal_metrics(
                scenario, simulation_results[scenario_id], goals, weights
            )
            analyses.append(analysis)

    analyses.sort(key=lambda a: a.total_utility, reverse=True)
    return analyses


def run_composed_analysis(
    scenarios: ComposedScenarioSet,
    registry: ComponentRegistry,
    goals: GoalSet,
    weight_preset: str = "balanced",
    n_simulations: int = 10000,
    random_seed: int = 42,
    affordability_pct: float = 0.30,
) -> Dict[str, Any]:
    """Run full analysis on composed scenarios.

    Args:
        scenarios: Set of composed scenarios
        registry: Component registry with all lookup tables
        goals: Goal definitions
        weight_preset: Weight preset ID
        n_simulations: Number of simulations
        random_seed: Random seed
        affordability_pct: Affordability percentage slider

    Returns:
        Dict with 'simulation_results', 'rankings', 'weights'
    """
    config = ComposedSimulationConfig(
        n_simulations=n_simulations,
        random_seed=random_seed,
        affordability_slider=affordability_pct,
    )

    runner = ComposedScenarioRunner(registry, config)
    simulation_results = runner.run_all_scenarios(scenarios, affordability_pct)

    # Get weights from preset
    preset = goals.presets.get(weight_preset, goals.presets.get("balanced"))
    weight_dict = preset.weights if preset else {f"G{i}": 1 / 6 for i in range(1, 7)}

    # Rank scenarios
    rankings = rank_scenarios_by_utility(scenarios, goals, weight_dict, simulation_results)

    return {
        "simulation_results": simulation_results,
        "rankings": rankings,
        "weights": weight_dict,
        "config": config,
    }
