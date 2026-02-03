"""Simulation Page for Hallar DSS - Supports both old and new scenario models."""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path

st.set_page_config(page_title="Simulation - Hallar DSS", page_icon="🔬", layout="wide")

st.title("🔬 Hermun / Monte Carlo Simulation")
st.markdown("*Run probabilistic analysis of development scenarios*")


def load_example_data():
    """Load example data for simulation."""
    from hallar.io.loaders import load_scenarios, load_markets, load_constraints, load_weights

    examples_dir = Path(__file__).parent.parent.parent / "data" / "examples"

    try:
        st.session_state.scenarios = load_scenarios(examples_dir / "scenarios_example.yaml")
        st.session_state.markets = load_markets(examples_dir / "market_scenarios.yaml")
        st.session_state.constraints = load_constraints(examples_dir / "constraints.yaml")
        st.session_state.weights = load_weights(examples_dir / "weights.yaml")
        return True
    except Exception as e:
        st.error(f"Failed to load example data: {e}")
        return False


def check_composed_data_loaded() -> bool:
    """Check if composed scenario data is loaded."""
    required = [
        "composed_scenarios",
        "ownership_structures",
        "financing_models",
        "byggingarrettur_options",
        "infrastructure_models",
        "counterparty_profiles",
        "hallar_params",
        "goals",
    ]
    return all(st.session_state.get(key) is not None for key in required)


def run_old_simulation(weights_dict, n_simulations, random_seed):
    """Run the Monte Carlo simulation with old Scenario model."""
    from hallar.simulation.monte_carlo import run_full_analysis
    from hallar.models.weights import WeightProfile

    weight_profile = WeightProfile(
        id="custom",
        name="Custom",
        weights=weights_dict,
    )

    with st.spinner(f"Running {n_simulations:,} simulations..."):
        results = run_full_analysis(
            scenarios=st.session_state.scenarios,
            markets=st.session_state.markets,
            constraints=st.session_state.constraints,
            weights=weight_profile,
            n_simulations=n_simulations,
            random_seed=random_seed,
        )

    return results


def run_composed_simulation(n_simulations, random_seed, weight_preset, affordability_pct):
    """Run Monte Carlo simulation on composed scenarios."""
    from hallar.simulation.composed_runner import (
        ComposedScenarioRunner,
        ComponentRegistry,
        ComposedSimulationConfig,
        run_composed_analysis,
    )

    # Build component registry
    registry = ComponentRegistry(
        ownership=st.session_state.ownership_structures,
        financing=st.session_state.financing_models,
        byggingarrettur=st.session_state.byggingarrettur_options,
        infrastructure=st.session_state.infrastructure_models,
        counterparties=st.session_state.counterparty_profiles,
        hallar_params=st.session_state.hallar_params,
    )

    # Run analysis
    with st.spinner(f"Running {n_simulations:,} simulations on composed scenarios..."):
        results = run_composed_analysis(
            scenarios=st.session_state.composed_scenarios,
            registry=registry,
            goals=st.session_state.goals,
            weight_preset=weight_preset,
            n_simulations=n_simulations,
            random_seed=random_seed,
            affordability_pct=affordability_pct,
        )

    return results


def render_old_simulation_results(results):
    """Render results from old simulation system."""
    st.subheader("📊 Simulation Results (Old System)")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Scenarios Evaluated", len(results.scenario_results))
    with col2:
        st.metric("Passed Constraints", len(results.passed_scenarios))
    with col3:
        st.metric("Simulations", f"{results.n_simulations:,}")
    with col4:
        if results.ranked_results:
            st.metric("Top Scenario", results.ranked_results[0].scenario.id)

    st.divider()

    # Top scenarios
    st.subheader("🏆 Top Scenarios")

    for i, result in enumerate(results.ranked_results[:5], 1):
        with st.container():
            cols = st.columns([1, 3, 2, 2, 2, 1])

            with cols[0]:
                st.markdown(f"### #{i}")

            with cols[1]:
                st.markdown(f"**{result.scenario.id}**: {result.scenario.name[:40]}")

            with cols[2]:
                st.metric("Utility", f"{result.utility:.3f}")

            with cols[3]:
                st.metric("E[NPV]", f"{result.metrics['expected_npv']:,.0f}M")

            with cols[4]:
                st.metric("P(Loss)", f"{result.metrics['prob_loss']:.1%}")

            with cols[5]:
                if result.passed_constraints:
                    st.success("✅")
                else:
                    st.error("❌")

        st.divider()

    # Full results table
    st.subheader("📋 Full Rankings")

    data = []
    for i, r in enumerate(results.ranked_results, 1):
        data.append({
            "Rank": i,
            "ID": r.scenario.id,
            "Name": r.scenario.name[:25] + "..." if len(r.scenario.name) > 25 else r.scenario.name,
            "Utility": round(r.utility, 3),
            "E[NPV]": round(r.metrics["expected_npv"], 0),
            "NPV Std": round(r.metrics["npv_std"], 0),
            "P(Loss)": f"{r.metrics['prob_loss']:.1%}",
            "CVaR 5%": round(r.metrics.get("cvar_05", 0), 0),
            "Time (mo)": round(r.metrics["expected_time"], 0),
            "Status": "PASS" if r.passed_constraints else "FAIL",
        })

    st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)


def render_composed_simulation_results(results):
    """Render results from composed scenario simulation."""
    sim_results = results["simulation_results"]
    rankings = results["rankings"]
    scenarios = st.session_state.composed_scenarios
    goals = st.session_state.goals

    st.subheader("📊 Simulation Results (ComposedScenario System)")

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Scenarios Simulated", len(sim_results))
    with col2:
        st.metric("Top Scenario", rankings[0].scenario_id if rankings else "N/A")
    with col3:
        if rankings:
            st.metric("Top Utility", f"{rankings[0].total_utility:.1f}")
    with col4:
        st.metric("Weight Profile", st.session_state.get("weight_preset", "balanced"))

    st.divider()

    # Top scenarios
    st.subheader("🏆 Top Scenarios")

    for i, analysis in enumerate(rankings[:5], 1):
        scenario = scenarios.scenarios[analysis.scenario_id]
        sim = sim_results[analysis.scenario_id]

        with st.container():
            cols = st.columns([1, 3, 2, 2, 2, 1])

            with cols[0]:
                st.markdown(f"### #{i}")

            with cols[1]:
                st.markdown(f"**{scenario.id}**: {scenario.name[:40]}")
                st.caption(f"Counterparty: {scenario.counterparty}")

            with cols[2]:
                st.metric("Utility", f"{analysis.total_utility:.1f}")

            with cols[3]:
                st.metric("E[NPV]", f"{sim.expected_npv:,.0f}M")

            with cols[4]:
                st.metric("P(Loss)", f"{sim.prob_loss:.1%}")

            with cols[5]:
                control = scenario.city_control_score
                if control >= 75:
                    st.success("🟢")
                elif control >= 50:
                    st.warning("🟡")
                else:
                    st.error("🔴")

        st.divider()

    # Full results table
    st.subheader("📋 Full Rankings")

    data = []
    for i, analysis in enumerate(rankings, 1):
        scenario = scenarios.scenarios[analysis.scenario_id]
        sim = sim_results[analysis.scenario_id]

        data.append({
            "Rank": i,
            "ID": scenario.id,
            "Name": scenario.name[:30] + "..." if len(scenario.name) > 30 else scenario.name,
            "Utility": round(analysis.total_utility, 1),
            "E[NPV]": round(sim.expected_npv, 0),
            "NPV Std": round(sim.npv_std, 0),
            "P(Loss)": f"{sim.prob_loss:.1%}",
            "CVaR 5%": round(sim.cvar_05, 0),
            "Time (mo)": round(sim.expected_time, 0),
            "Control": f"{scenario.city_control_score}%",
            "Counterparty": scenario.counterparty,
        })

    st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

    # Goal breakdown for top scenario
    st.divider()
    st.subheader("🎯 Goal Breakdown - Top Scenario")

    if rankings:
        top_analysis = rankings[0]

        goal_data = []
        for gid, metric in top_analysis.metrics.items():
            goal = goals.goals.get(gid)
            goal_data.append({
                "Goal": goal.name_en if goal else gid,
                "Raw Value": round(metric.raw_value, 1),
                "Normalized": round(metric.normalized_score, 1),
                "Weight": f"{results['weights'].get(gid, 0):.0%}",
                "Contribution": round(metric.weighted_contribution, 2),
            })

        st.dataframe(pd.DataFrame(goal_data), hide_index=True, use_container_width=True)


def main():
    # Check what data is available
    has_old_data = all([
        st.session_state.get("scenarios"),
        st.session_state.get("markets"),
        st.session_state.get("constraints"),
    ])
    has_composed_data = check_composed_data_loaded()

    # Mode selection
    mode = "composed" if has_composed_data else "old"
    if has_old_data and has_composed_data:
        mode = st.radio(
            "Simulation Mode",
            ["composed", "old"],
            format_func=lambda x: "ComposedScenario (6 Goals)" if x == "composed" else "Original Scenario (4 Goals)",
            horizontal=True,
        )

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Simulation Settings")

        n_simulations = st.number_input(
            "Number of Simulations",
            min_value=100,
            max_value=100000,
            value=st.session_state.get("n_simulations", 10000),
            step=1000,
        )
        st.session_state.n_simulations = n_simulations

        random_seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=999999,
            value=st.session_state.get("random_seed", 42),
        )
        st.session_state.random_seed = random_seed

        st.divider()

        if mode == "composed" and has_composed_data:
            st.header("🏠 Affordability Setting")
            affordability_pct = st.slider(
                "Affordable Housing %",
                min_value=0,
                max_value=60,
                value=30,
                step=5,
                help="Percentage of units designated as affordable housing",
            )
            st.caption(f"Selected: {affordability_pct}% affordable units")

            st.divider()

            st.header("⚖️ Goal Weights")

            # Get available presets
            goals = st.session_state.goals
            preset_options = list(goals.presets.keys())

            weight_preset = st.selectbox(
                "Weight Preset",
                options=preset_options,
                index=preset_options.index(st.session_state.get("weight_preset", "balanced"))
                      if st.session_state.get("weight_preset", "balanced") in preset_options else 0,
                format_func=lambda x: goals.presets[x].name_en if x in goals.presets else x,
            )
            st.session_state.weight_preset = weight_preset

            # Show weights
            if weight_preset in goals.presets:
                preset = goals.presets[weight_preset]
                st.caption("Weights:")
                for gid, weight in preset.weights.items():
                    goal_name = goals.goals[gid].name_en if gid in goals.goals else gid
                    st.caption(f"  {goal_name}: {weight:.0%}")
        else:
            st.header("⚖️ Goal Weights")

            # Manual weight sliders for old system
            weights_dict = {"speed": 0.25, "affordability": 0.25, "quality": 0.25, "financial": 0.25}

            w_speed = st.slider("Speed", 0.0, 1.0, weights_dict.get("speed", 0.25))
            w_afford = st.slider("Affordability", 0.0, 1.0, weights_dict.get("affordability", 0.25))
            w_quality = st.slider("Quality", 0.0, 1.0, weights_dict.get("quality", 0.25))
            w_financial = st.slider("Financial", 0.0, 1.0, weights_dict.get("financial", 0.25))

            total = w_speed + w_afford + w_quality + w_financial
            if total > 0:
                weights_dict = {
                    "speed": w_speed / total,
                    "affordability": w_afford / total,
                    "quality": w_quality / total,
                    "financial": w_financial / total,
                }

            st.caption(f"Normalized: S={weights_dict['speed']:.0%}, A={weights_dict['affordability']:.0%}, Q={weights_dict['quality']:.0%}, F={weights_dict['financial']:.0%}")
            affordability_pct = 30
            weight_preset = "balanced"

    # Main content
    if mode == "old" and not has_old_data:
        st.warning("Original simulation data not loaded. Load example data to run simulation.")

        if st.button("📥 Load Example Data", type="primary"):
            if load_example_data():
                st.success("Example data loaded successfully!")
                st.rerun()
        return

    if mode == "composed" and not has_composed_data:
        st.warning("Composed scenario data not loaded. Please return to home page to load data.")
        return

    # Data status
    if mode == "composed":
        scenarios = st.session_state.composed_scenarios
        st.success(f"✅ {len(scenarios.scenarios)} composed scenarios loaded")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"✅ {len(st.session_state.scenarios)} scenarios loaded")
        with col2:
            st.success(f"✅ {len(st.session_state.markets)} market scenarios loaded")
        with col3:
            st.success(f"✅ {len(st.session_state.constraints.constraints)} constraints loaded")

    st.divider()

    # Run simulation button
    if st.button("▶️ Run Simulation", type="primary", use_container_width=True):
        if mode == "composed":
            results = run_composed_simulation(
                n_simulations=n_simulations,
                random_seed=random_seed,
                weight_preset=weight_preset,
                affordability_pct=affordability_pct / 100.0,
            )
            st.session_state.composed_simulation_results = results
        else:
            results = run_old_simulation(weights_dict, n_simulations, random_seed)
            st.session_state.results = results
        st.success("Simulation complete!")
        st.rerun()

    # Display results
    if mode == "composed" and st.session_state.get("composed_simulation_results"):
        render_composed_simulation_results(st.session_state.composed_simulation_results)
    elif mode == "old" and st.session_state.get("results"):
        render_old_simulation_results(st.session_state.results)


if __name__ == "__main__":
    main()
