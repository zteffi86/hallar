"""Monte Carlo simulation engine for Hallar DSS."""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from hallar.models.scenario import Scenario, PERTParams
from hallar.models.market import MarketScenario
from hallar.models.constraints import ConstraintSet
from hallar.models.weights import WeightProfile
from hallar.simulation.distributions import pert_distribution, pert_sample
from hallar.simulation.npv import calculate_npv, calculate_risk_adjusted_npv
from hallar.simulation.utility import (
    calculate_utility,
    calculate_objective_metrics,
    update_normalization_from_results,
    DEFAULT_NORMALIZATION,
    NormalizationParams,
)


@dataclass
class SimulationResults:
    """Results from a single scenario simulation."""

    npv: np.ndarray
    first_units_months: np.ndarray
    first_school_months: np.ndarray
    sixty_percent_months: np.ndarray
    total_cost: np.ndarray
    total_revenue: np.ndarray
    quality_score: np.ndarray
    affordability_score: np.ndarray
    developer_defaulted: np.ndarray

    def to_dict(self) -> Dict[str, np.ndarray]:
        """Convert to dictionary of arrays."""
        return {
            "npv": self.npv,
            "first_units_months": self.first_units_months,
            "first_school_months": self.first_school_months,
            "sixty_percent_months": self.sixty_percent_months,
            "total_cost": self.total_cost,
            "total_revenue": self.total_revenue,
            "quality_score": self.quality_score,
            "affordability_score": self.affordability_score,
            "developer_defaulted": self.developer_defaulted,
        }


@dataclass
class ScenarioResult:
    """Complete analysis result for a single scenario."""

    scenario: Scenario
    simulation_results: SimulationResults
    metrics: Dict[str, float]
    utility: float
    passed_constraints: bool
    constraint_violations: List[Tuple[str, str]]
    market_results: Optional[Dict[str, SimulationResults]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "scenario_id": self.scenario.id,
            "scenario_name": self.scenario.name,
            "metrics": self.metrics,
            "utility": self.utility,
            "passed_constraints": self.passed_constraints,
            "constraint_violations": self.constraint_violations,
        }


@dataclass
class FullAnalysisResults:
    """Complete analysis results across all scenarios."""

    scenario_results: List[ScenarioResult]
    ranked_results: List[ScenarioResult]
    weight_profile: WeightProfile
    n_simulations: int
    random_seed: int
    normalization_params: Dict[str, NormalizationParams]
    weight_sensitivity: Optional[Dict[str, Dict[str, float]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "n_simulations": self.n_simulations,
            "random_seed": self.random_seed,
            "weight_profile": {
                "id": self.weight_profile.id,
                "name": self.weight_profile.name,
                "weights": self.weight_profile.weights,
            },
            "results": [r.to_dict() for r in self.ranked_results],
            "weight_sensitivity": self.weight_sensitivity,
        }

    @property
    def top_3(self) -> List[ScenarioResult]:
        """Get top 3 scenarios by utility."""
        return self.ranked_results[:3]

    @property
    def passed_scenarios(self) -> List[ScenarioResult]:
        """Get scenarios that passed all constraints."""
        return [r for r in self.ranked_results if r.passed_constraints]

    @property
    def failed_scenarios(self) -> List[ScenarioResult]:
        """Get scenarios that failed constraints."""
        return [r for r in self.ranked_results if not r.passed_constraints]


class MonteCarloSimulation:
    """Monte Carlo simulation engine."""

    def __init__(
        self,
        n_simulations: int = 10000,
        random_seed: int = 42,
    ):
        """
        Initialize simulation engine.

        Args:
            n_simulations: Number of Monte Carlo iterations
            random_seed: Random seed for reproducibility
        """
        self.n_simulations = n_simulations
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)

    def _sample_pert(self, params: PERTParams) -> np.ndarray:
        """Sample from PERT distribution."""
        return pert_distribution(
            params.min, params.likely, params.max,
            samples=self.n_simulations, rng=self.rng
        )

    def _sample_pert_single(self, params: PERTParams) -> float:
        """Sample single value from PERT distribution."""
        return pert_sample(params, rng=self.rng)

    def run_scenario(
        self,
        scenario: Scenario,
        market: MarketScenario,
    ) -> SimulationResults:
        """
        Run Monte Carlo simulation for a single scenario under a single market condition.

        Args:
            scenario: Scenario definition
            market: Market condition

        Returns:
            SimulationResults with distributions of all metrics
        """
        n = self.n_simulations
        params = market.parameters

        # Initialize result arrays
        npv = np.zeros(n)
        first_units_months = np.zeros(n)
        first_school_months = np.zeros(n)
        sixty_percent_months = np.zeros(n)
        total_cost = np.zeros(n)
        total_revenue = np.zeros(n)
        quality_score = np.zeros(n)
        affordability_score = np.zeros(n)
        developer_defaulted = np.zeros(n, dtype=bool)

        # Sample base distributions
        base_cost = self._sample_pert(scenario.infrastructure_cost)
        base_revenue = self._sample_pert(scenario.rights_revenue)
        base_first_units = self._sample_pert(scenario.timeline.first_units)
        base_first_school = self._sample_pert(scenario.timeline.first_school)
        base_sixty_pct = self._sample_pert(scenario.timeline.sixty_percent_complete)

        # Sample risk events
        cost_overrun_events = self.rng.random(n) < scenario.risks.cost_overrun_probability
        cost_overrun_multipliers = self._sample_pert(scenario.risks.cost_overrun_multiplier)

        delay_events = self.rng.random(n) < scenario.risks.delay_probability
        delay_amounts = self._sample_pert(scenario.risks.delay_months)

        # Developer default probability (adjusted by market condition)
        default_prob = scenario.risks.developer_default_probability * params.developer_default_multiplier
        default_events = self.rng.random(n) < default_prob

        # Sample quality defect rate
        defect_rates = self._sample_pert(scenario.quality.defect_rate)

        # Energy rating to score mapping
        energy_scores = {"A+": 100, "A": 90, "B": 70, "C": 50, "D": 30, "E": 20, "F": 10, "G": 5}
        base_energy_score = energy_scores.get(scenario.quality.energy_rating, 50)

        for i in range(n):
            # Calculate cost
            cost = base_cost[i] * params.construction_cost_multiplier
            if cost_overrun_events[i]:
                cost *= cost_overrun_multipliers[i]

            # Calculate timeline
            first_units = base_first_units[i]
            first_school = base_first_school[i]
            sixty_pct = base_sixty_pct[i]

            if delay_events[i]:
                delay = delay_amounts[i]
                first_units += delay
                first_school += delay
                sixty_pct += delay

            # Handle developer default
            if default_events[i] and scenario.step_in_cost_fraction > 0:
                developer_defaulted[i] = True
                # Add step-in costs (fraction of remaining work)
                completion_at_default = self.rng.uniform(0.3, 0.7)
                remaining_cost = cost * (1 - completion_at_default)
                step_in_cost = remaining_cost * scenario.step_in_cost_fraction
                cost += step_in_cost
                # Add delays for finding new developer
                first_units += 18
                first_school += 18
                sixty_pct += 24

            # Calculate revenue with property price growth
            years_to_sale = sixty_pct / 12
            price_adjustment = (1 + params.property_price_growth) ** years_to_sale
            revenue = base_revenue[i] * price_adjustment

            # Calculate NPV
            discount_rate = params.interest_rate / 12  # Monthly rate

            # Build cash flow model
            cash_flows = []
            periods = []

            # Costs spread over construction period (monthly)
            construction_months = int(sixty_pct)
            if construction_months > 0:
                monthly_cost = cost / construction_months
                for month in range(construction_months):
                    cash_flows.append(-monthly_cost)
                    periods.append(month)

            # Revenue at sale (when 60% complete)
            sale_month = int(sixty_pct)
            cash_flows.append(revenue)
            periods.append(sale_month)

            # JV adjustments if applicable - replace entire cash flow model
            if scenario.jv_params is not None:
                jv = scenario.jv_params
                project_profit = revenue - cost

                if project_profit > 0:
                    city_share = project_profit * jv.profit_share
                else:
                    city_share = project_profit * jv.loss_share

                # For JV: city invests equity, receives profit share (not full revenue)
                equity_investment = cost * jv.city_equity_share

                # Replace cash flow model entirely for JV
                cash_flows = []
                periods = []

                # Equity investment at start
                cash_flows.append(-equity_investment)
                periods.append(0)

                # Return of equity + profit share at end
                cash_flows.append(equity_investment + city_share)
                periods.append(sale_month)

                # Management fees (annual)
                for year in range(max(1, int(sixty_pct / 12))):
                    cash_flows.append(-jv.management_fee_annual)
                    periods.append(year * 12)

            # Calculate NPV
            if periods:
                npv_val = calculate_npv(cash_flows, discount_rate, periods)
            else:
                npv_val = revenue - cost

            # Quality score
            quality = max(0, base_energy_score - defect_rates[i] * 100)

            # Affordability score
            aff = scenario.affordability
            affordability = (
                aff.percentage_affordable * 40 +
                aff.price_discount * 30 +
                min(aff.restriction_years / 50, 1) * 20 +
                (10 if aff.legally_binding else 0)
            )

            # Store results
            npv[i] = npv_val
            first_units_months[i] = first_units
            first_school_months[i] = first_school
            sixty_percent_months[i] = sixty_pct
            total_cost[i] = cost
            total_revenue[i] = revenue
            quality_score[i] = quality
            affordability_score[i] = affordability

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
        )

    def run_scenario_all_markets(
        self,
        scenario: Scenario,
        markets: List[MarketScenario],
    ) -> Tuple[SimulationResults, Dict[str, SimulationResults]]:
        """
        Run simulation for a scenario across all market conditions.

        Uses proportional sampling based on market probabilities to preserve
        variance structure and properly estimate risk.

        Args:
            scenario: Scenario definition
            markets: List of market scenarios

        Returns:
            Tuple of (combined results, dict of per-market results)
        """
        total_prob = sum(m.probability for m in markets)

        # Initialize lists to collect samples proportionally
        combined_arrays: Dict[str, list] = {
            'npv': [],
            'first_units_months': [],
            'first_school_months': [],
            'sixty_percent_months': [],
            'total_cost': [],
            'total_revenue': [],
            'quality_score': [],
            'affordability_score': [],
            'developer_defaulted': [],
        }
        market_results = {}

        # Run simulation for each market and sample proportionally
        for market in markets:
            results = self.run_scenario(scenario, market)
            market_results[market.id] = results

            # Sample proportionally to market probability
            n_samples = max(1, int(self.n_simulations * market.probability / total_prob))
            indices = self.rng.choice(self.n_simulations, size=n_samples, replace=False)

            combined_arrays['npv'].extend(results.npv[indices])
            combined_arrays['first_units_months'].extend(results.first_units_months[indices])
            combined_arrays['first_school_months'].extend(results.first_school_months[indices])
            combined_arrays['sixty_percent_months'].extend(results.sixty_percent_months[indices])
            combined_arrays['total_cost'].extend(results.total_cost[indices])
            combined_arrays['total_revenue'].extend(results.total_revenue[indices])
            combined_arrays['quality_score'].extend(results.quality_score[indices])
            combined_arrays['affordability_score'].extend(results.affordability_score[indices])
            combined_arrays['developer_defaulted'].extend(results.developer_defaulted[indices])

        combined_results = SimulationResults(
            npv=np.array(combined_arrays['npv']),
            first_units_months=np.array(combined_arrays['first_units_months']),
            first_school_months=np.array(combined_arrays['first_school_months']),
            sixty_percent_months=np.array(combined_arrays['sixty_percent_months']),
            total_cost=np.array(combined_arrays['total_cost']),
            total_revenue=np.array(combined_arrays['total_revenue']),
            quality_score=np.array(combined_arrays['quality_score']),
            affordability_score=np.array(combined_arrays['affordability_score']),
            developer_defaulted=np.array(combined_arrays['developer_defaulted'], dtype=bool),
        )

        return combined_results, market_results


def run_simulation(
    scenario: Scenario,
    market: MarketScenario,
    n_simulations: int = 10000,
    random_seed: int = 42,
) -> SimulationResults:
    """
    Convenience function to run simulation for a single scenario/market pair.

    Args:
        scenario: Scenario definition
        market: Market condition
        n_simulations: Number of Monte Carlo iterations
        random_seed: Random seed for reproducibility

    Returns:
        SimulationResults
    """
    engine = MonteCarloSimulation(n_simulations=n_simulations, random_seed=random_seed)
    return engine.run_scenario(scenario, market)


def run_full_analysis(
    scenarios: List[Scenario],
    markets: List[MarketScenario],
    constraints: ConstraintSet,
    weights: WeightProfile,
    n_simulations: int = 10000,
    random_seed: int = 42,
) -> FullAnalysisResults:
    """
    Run complete analysis across all scenarios, markets, and constraints.

    Args:
        scenarios: List of scenario definitions
        markets: List of market scenarios
        constraints: Constraint set for filtering
        weights: Weight profile for utility calculation
        n_simulations: Number of Monte Carlo iterations
        random_seed: Random seed for reproducibility

    Returns:
        FullAnalysisResults with rankings and metrics
    """
    engine = MonteCarloSimulation(n_simulations=n_simulations, random_seed=random_seed)

    # Run simulations for all scenarios
    scenario_results = []

    for scenario in scenarios:
        # Run across all markets
        combined_results, market_results = engine.run_scenario_all_markets(scenario, markets)

        # Calculate risk-adjusted metrics
        npv_metrics = calculate_risk_adjusted_npv(combined_results.npv)

        # Aggregate metrics
        metrics = {
            "expected_npv": npv_metrics["expected_npv"],
            "npv_std": npv_metrics["std_dev"],
            "npv_p10": npv_metrics["percentile_10"],
            "npv_p90": npv_metrics["percentile_90"],
            "cvar_05": npv_metrics["cvar_05"],
            "prob_loss": npv_metrics["prob_loss"],
            "expected_time": float(np.mean(combined_results.sixty_percent_months)),
            "time_p10": float(np.percentile(combined_results.sixty_percent_months, 10)),
            "time_p90": float(np.percentile(combined_results.sixty_percent_months, 90)),
            "expected_first_units": float(np.mean(combined_results.first_units_months)),
            "expected_first_school": float(np.mean(combined_results.first_school_months)),
            "quality_score": float(np.mean(combined_results.quality_score)),
            "affordability_score": float(np.mean(combined_results.affordability_score)),
            "default_rate": float(np.mean(combined_results.developer_defaulted)),
        }

        # Check constraints
        sim_dict = combined_results.to_dict()
        deterministic_values = {
            "affordable_percentage": scenario.affordability.percentage_affordable,
            "restriction_years": scenario.affordability.restriction_years,
            "energy_rating": scenario.quality.energy_rating,
            "rental_percentage": scenario.affordability.rental_percentage,
        }

        passed, violations = constraints.check_all(sim_dict, deterministic_values)

        # Create result object (utility calculated later after normalization)
        result = ScenarioResult(
            scenario=scenario,
            simulation_results=combined_results,
            metrics=metrics,
            utility=0.0,  # Placeholder
            passed_constraints=passed,
            constraint_violations=violations,
            market_results=market_results,
        )
        scenario_results.append(result)

    # Update normalization parameters based on actual results
    normalization_params = update_normalization_from_results(scenario_results)

    # Calculate utility scores with updated normalization
    for result in scenario_results:
        objective_metrics = {
            "speed": result.metrics["expected_time"],
            "affordability": result.metrics["affordability_score"],
            "quality": result.metrics["quality_score"],
            "financial": result.metrics["expected_npv"],
        }
        result.utility = calculate_utility(
            objective_metrics,
            weights.weights,
            normalization_params,
        )

    # Rank scenarios by utility (highest first)
    ranked_results = sorted(scenario_results, key=lambda r: r.utility, reverse=True)

    return FullAnalysisResults(
        scenario_results=scenario_results,
        ranked_results=ranked_results,
        weight_profile=weights,
        n_simulations=n_simulations,
        random_seed=random_seed,
        normalization_params=normalization_params,
    )
