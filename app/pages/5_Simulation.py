"""Simulation Page for Hallar DSS."""

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


def run_simulation(weights_dict, n_simulations, random_seed):
    """Run the Monte Carlo simulation."""
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


def main():
    # Check if original simulation data is available
    has_sim_data = all([
        st.session_state.get("scenarios"),
        st.session_state.get("markets"),
        st.session_state.get("constraints"),
    ])

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

        st.header("⚖️ Goal Weights")

        # Get weights from session state
        goals = st.session_state.get("goals")
        if goals and st.session_state.get("weight_preset") in goals.presets:
            preset = goals.presets[st.session_state.weight_preset]
            weights_dict = {
                "speed": preset.weights.get("G1", 0.167),
                "affordability": preset.weights.get("G2", 0.167),
                "quality": preset.weights.get("G3", 0.167),
                "financial": preset.weights.get("G4", 0.167),
            }
        else:
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

    # Main content
    if not has_sim_data:
        st.warning("Simulation data not loaded. Load example data to run simulation.")

        if st.button("📥 Load Example Data", type="primary"):
            if load_example_data():
                st.success("Example data loaded successfully!")
                st.rerun()
        return

    # Data status
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
        results = run_simulation(weights_dict, n_simulations, random_seed)
        st.session_state.results = results
        st.success("Simulation complete!")
        st.rerun()

    # Display results
    if st.session_state.get("results"):
        results = st.session_state.results

        st.subheader("📊 Simulation Results")

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
                "Name": r.scenario.name[:25] + "...",
                "Utility": round(r.utility, 3),
                "E[NPV]": round(r.metrics["expected_npv"], 0),
                "NPV Std": round(r.metrics["npv_std"], 0),
                "P(Loss)": f"{r.metrics['prob_loss']:.1%}",
                "CVaR 5%": round(r.metrics.get("cvar_05", 0), 0),
                "Time (mo)": round(r.metrics["expected_time"], 0),
                "Status": "PASS" if r.passed_constraints else "FAIL",
            })

        st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        # Constraint violations
        st.divider()
        st.subheader("🚫 Constraint Violations")

        failed = [r for r in results.scenario_results if not r.passed_constraints]
        if failed:
            for r in failed:
                with st.expander(f"❌ {r.scenario.id}: {r.scenario.name}"):
                    for vid, vmsg in r.constraint_violations:
                        st.markdown(f"- {vmsg}")
        else:
            st.success("All scenarios passed constraints!")


if __name__ == "__main__":
    main()
