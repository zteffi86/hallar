"""Streamlit web interface for Hallar DSS."""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import yaml

# Set page config first
st.set_page_config(
    page_title="Hallar DSS",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_data():
    """Load data from files or session state."""
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = None
    if "markets" not in st.session_state:
        st.session_state.markets = None
    if "constraints" not in st.session_state:
        st.session_state.constraints = None
    if "weights" not in st.session_state:
        st.session_state.weights = None
    if "results" not in st.session_state:
        st.session_state.results = None


def main():
    """Main Streamlit application."""
    load_data()

    st.title("🏗️ Hallar Decision Support System")
    st.markdown("*Quantitative analysis for land development scenarios*")

    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Data input section
        st.subheader("📁 Data Input")

        # File uploaders
        scenarios_file = st.file_uploader(
            "Scenarios YAML",
            type=["yaml", "yml"],
            key="scenarios_upload",
        )

        markets_file = st.file_uploader(
            "Market Scenarios YAML",
            type=["yaml", "yml"],
            key="markets_upload",
        )

        constraints_file = st.file_uploader(
            "Constraints YAML",
            type=["yaml", "yml"],
            key="constraints_upload",
        )

        weights_file = st.file_uploader(
            "Weights YAML (optional)",
            type=["yaml", "yml"],
            key="weights_upload",
        )

        # Load example data button
        if st.button("📥 Load Example Data"):
            load_example_data()
            st.success("Example data loaded!")
            st.rerun()

        st.divider()

        # Weight profile selection
        st.subheader("⚖️ Weight Profile")

        weight_options = ["Balanced", "Housing Crisis", "Speed Priority", "Quality Priority", "Custom"]
        weight_selection = st.selectbox("Select Profile", weight_options)

        if weight_selection == "Custom":
            st.markdown("*Adjust weights (will be normalized)*")
            w_speed = st.slider("Speed", 0.0, 1.0, 0.25, key="w_speed")
            w_afford = st.slider("Affordability", 0.0, 1.0, 0.25, key="w_afford")
            w_quality = st.slider("Quality", 0.0, 1.0, 0.25, key="w_quality")
            w_financial = st.slider("Financial", 0.0, 1.0, 0.25, key="w_financial")

            # Normalize and show
            total = w_speed + w_afford + w_quality + w_financial
            if total > 0:
                weights_dict = {
                    "speed": w_speed / total,
                    "affordability": w_afford / total,
                    "quality": w_quality / total,
                    "financial": w_financial / total,
                }
                st.caption(f"Normalized: S={weights_dict['speed']:.0%}, A={weights_dict['affordability']:.0%}, Q={weights_dict['quality']:.0%}, F={weights_dict['financial']:.0%}")
        else:
            weights_dict = get_preset_weights(weight_selection)

        st.divider()

        # Simulation settings
        st.subheader("🎲 Simulation Settings")
        n_simulations = st.number_input(
            "Number of Simulations",
            min_value=100,
            max_value=100000,
            value=10000,
            step=1000,
        )
        random_seed = st.number_input(
            "Random Seed",
            min_value=0,
            max_value=999999,
            value=42,
        )

    # Process uploaded files
    if scenarios_file:
        process_uploaded_file(scenarios_file, "scenarios")
    if markets_file:
        process_uploaded_file(markets_file, "markets")
    if constraints_file:
        process_uploaded_file(constraints_file, "constraints")
    if weights_file:
        process_uploaded_file(weights_file, "weights")

    # Main content area - tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Data", "🔬 Results", "📈 Analysis", "📥 Export"])

    with tab1:
        render_data_tab()

    with tab2:
        render_results_tab(weights_dict, n_simulations, random_seed)

    with tab3:
        render_analysis_tab()

    with tab4:
        render_export_tab()


def get_preset_weights(selection: str) -> dict:
    """Get preset weight configurations."""
    presets = {
        "Balanced": {"speed": 0.30, "affordability": 0.30, "quality": 0.30, "financial": 0.10},
        "Housing Crisis": {"speed": 0.25, "affordability": 0.40, "quality": 0.20, "financial": 0.15},
        "Speed Priority": {"speed": 0.45, "affordability": 0.20, "quality": 0.20, "financial": 0.15},
        "Quality Priority": {"speed": 0.20, "affordability": 0.20, "quality": 0.45, "financial": 0.15},
    }
    return presets.get(selection, presets["Balanced"])


def load_example_data():
    """Load example data files into session state."""
    from hallar.io.loaders import load_scenarios, load_markets, load_constraints, load_weights

    examples_dir = Path(__file__).parent.parent / "data" / "examples"

    try:
        st.session_state.scenarios = load_scenarios(examples_dir / "scenarios_example.yaml")
        st.session_state.markets = load_markets(examples_dir / "market_scenarios.yaml")
        st.session_state.constraints = load_constraints(examples_dir / "constraints.yaml")
        st.session_state.weights = load_weights(examples_dir / "weights.yaml")
    except Exception as e:
        st.error(f"Failed to load example data: {e}")


def process_uploaded_file(file, data_type: str):
    """Process an uploaded YAML file."""
    from hallar.io.loaders import load_scenarios, load_markets, load_constraints, load_weights

    try:
        if data_type == "scenarios":
            st.session_state.scenarios = load_scenarios(file)
        elif data_type == "markets":
            st.session_state.markets = load_markets(file)
        elif data_type == "constraints":
            st.session_state.constraints = load_constraints(file)
        elif data_type == "weights":
            st.session_state.weights = load_weights(file)
    except Exception as e:
        st.error(f"Error loading {data_type}: {e}")


def render_data_tab():
    """Render the data input/review tab."""
    st.header("📊 Data Overview")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Scenarios")
        if st.session_state.scenarios:
            scenarios = st.session_state.scenarios
            st.success(f"✅ {len(scenarios)} scenarios loaded")

            # Show scenario summary
            data = []
            for s in scenarios:
                data.append({
                    "ID": s.id,
                    "Name": s.name[:30] + "..." if len(s.name) > 30 else s.name,
                    "Infra Cost (likely)": f"{s.infrastructure_cost.likely:,.0f}M",
                    "Revenue (likely)": f"{s.rights_revenue.likely:,.0f}M",
                    "Affordable %": f"{s.affordability.percentage_affordable:.0%}",
                })
            st.dataframe(pd.DataFrame(data), hide_index=True)

            # Expandable details
            with st.expander("View Scenario Details"):
                selected = st.selectbox(
                    "Select Scenario",
                    options=[s.id for s in scenarios],
                )
                scenario = next(s for s in scenarios if s.id == selected)
                st.json(scenario.to_dict())
        else:
            st.warning("No scenarios loaded")

        st.subheader("Constraints")
        if st.session_state.constraints:
            constraints = st.session_state.constraints
            st.success(f"✅ {len(constraints.constraints)} constraints loaded")

            data = []
            for cid, c in constraints.constraints.items():
                data.append({
                    "ID": cid,
                    "Name": c.name,
                    "Type": c.type.value,
                    "Threshold": str(c.threshold),
                })
            st.dataframe(pd.DataFrame(data), hide_index=True)
        else:
            st.warning("No constraints loaded")

    with col2:
        st.subheader("Market Scenarios")
        if st.session_state.markets:
            markets = st.session_state.markets
            st.success(f"✅ {len(markets)} market scenarios loaded")

            data = []
            for m in markets:
                data.append({
                    "ID": m.id,
                    "Name": m.name,
                    "Probability": f"{m.probability:.0%}",
                    "Cost Mult.": f"{m.parameters.construction_cost_multiplier:.2f}",
                    "Interest": f"{m.parameters.interest_rate:.1%}",
                })
            st.dataframe(pd.DataFrame(data), hide_index=True)
        else:
            st.warning("No market scenarios loaded")

        st.subheader("Weight Profiles")
        if st.session_state.weights:
            weights = st.session_state.weights
            st.success(f"✅ {len(weights)} weight profiles loaded")

            data = []
            for w in weights:
                data.append({
                    "ID": w.id,
                    "Name": w.name,
                    "Speed": f"{w.weights['speed']:.0%}",
                    "Afford.": f"{w.weights['affordability']:.0%}",
                    "Quality": f"{w.weights['quality']:.0%}",
                    "Financial": f"{w.weights['financial']:.0%}",
                })
            st.dataframe(pd.DataFrame(data), hide_index=True)
        else:
            st.info("Using preset weight profiles")


def render_results_tab(weights_dict: dict, n_simulations: int, random_seed: int):
    """Render the results tab."""
    st.header("🔬 Simulation Results")

    # Check if data is loaded
    if not all([st.session_state.scenarios, st.session_state.markets, st.session_state.constraints]):
        st.warning("Please load all required data files first (Scenarios, Markets, Constraints)")
        return

    # Run simulation button
    if st.button("▶️ Run Simulation", type="primary", use_container_width=True):
        run_simulation(weights_dict, n_simulations, random_seed)

    # Display results
    if st.session_state.results:
        results = st.session_state.results

        # Summary metrics
        st.subheader("Summary")
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

        for i, result in enumerate(results.ranked_results[:3], 1):
            with st.container():
                cols = st.columns([1, 4, 2, 2, 2, 2])

                with cols[0]:
                    st.markdown(f"### #{i}")

                with cols[1]:
                    st.markdown(f"**{result.scenario.id}**: {result.scenario.name}")
                    st.caption(result.scenario.description[:100] + "..." if len(result.scenario.description) > 100 else result.scenario.description)

                with cols[2]:
                    st.metric("Utility", f"{result.utility:.3f}")

                with cols[3]:
                    st.metric("E[NPV]", f"{result.metrics['expected_npv']:,.0f}M")

                with cols[4]:
                    st.metric("P(Loss)", f"{result.metrics['prob_loss']:.1%}")

                with cols[5]:
                    if result.passed_constraints:
                        st.success("✅ PASS")
                    else:
                        st.error("❌ FAIL")

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
                "Time (mo)": round(r.metrics["expected_time"], 0),
                "Quality": round(r.metrics["quality_score"], 1),
                "Afford.": round(r.metrics["affordability_score"], 1),
                "Status": "PASS" if r.passed_constraints else "FAIL",
            })

        df = pd.DataFrame(data)
        st.dataframe(
            df,
            hide_index=True,
            column_config={
                "E[NPV]": st.column_config.NumberColumn(format="%d M"),
                "NPV Std": st.column_config.NumberColumn(format="%d M"),
            }
        )


def run_simulation(weights_dict: dict, n_simulations: int, random_seed: int):
    """Run the Monte Carlo simulation."""
    from hallar.simulation.monte_carlo import run_full_analysis
    from hallar.models.weights import WeightProfile

    # Create weight profile
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

    st.session_state.results = results
    st.success("Simulation complete!")


def render_analysis_tab():
    """Render the analysis tab with charts."""
    st.header("📈 Analysis")

    if not st.session_state.results:
        st.warning("Run simulation first to see analysis")
        return

    results = st.session_state.results

    # Chart selection
    chart_type = st.selectbox(
        "Select Visualization",
        ["Utility Ranking", "NPV Distribution", "Radar Comparison", "Pareto Frontier", "Timeline Distribution"]
    )

    if chart_type == "Utility Ranking":
        from hallar.visualization.charts import create_ranking_bar_chart
        try:
            fig = create_ranking_bar_chart(results, use_plotly=True)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {e}")

    elif chart_type == "NPV Distribution":
        from hallar.visualization.charts import create_npv_distribution_chart
        scenario_ids = st.multiselect(
            "Select Scenarios",
            options=[r.scenario.id for r in results.scenario_results],
            default=[r.scenario.id for r in results.ranked_results[:3]],
        )
        if scenario_ids:
            try:
                fig = create_npv_distribution_chart(results, scenario_ids=scenario_ids, use_plotly=True)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating chart: {e}")

    elif chart_type == "Radar Comparison":
        from hallar.visualization.charts import create_scenario_comparison_radar
        scenario_ids = st.multiselect(
            "Select Scenarios to Compare",
            options=[r.scenario.id for r in results.scenario_results],
            default=[r.scenario.id for r in results.ranked_results[:3]],
            max_selections=5,
        )
        if scenario_ids:
            try:
                fig = create_scenario_comparison_radar(results, scenario_ids=scenario_ids, use_plotly=True)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating chart: {e}")

    elif chart_type == "Pareto Frontier":
        from hallar.visualization.charts import create_pareto_frontier_plot
        col1, col2 = st.columns(2)
        with col1:
            x_obj = st.selectbox("X-Axis", ["expected_npv", "expected_time", "quality_score", "affordability_score"])
        with col2:
            y_obj = st.selectbox("Y-Axis", ["expected_time", "expected_npv", "quality_score", "affordability_score"])
        try:
            fig = create_pareto_frontier_plot(results, x_objective=x_obj, y_objective=y_obj, use_plotly=True)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {e}")

    elif chart_type == "Timeline Distribution":
        from hallar.visualization.charts import create_timeline_chart
        try:
            fig = create_timeline_chart(results, use_plotly=True)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating chart: {e}")

    # Constraint violations
    st.divider()
    st.subheader("Constraint Details")

    failed = [r for r in results.scenario_results if not r.passed_constraints]
    if failed:
        st.error(f"**{len(failed)} scenarios failed constraints:**")
        for r in failed:
            with st.expander(f"❌ {r.scenario.id}: {r.scenario.name}"):
                for vid, vmsg in r.constraint_violations:
                    st.markdown(f"- {vmsg}")
    else:
        st.success("All scenarios passed constraints!")


def render_export_tab():
    """Render the export tab."""
    st.header("📥 Export Results")

    if not st.session_state.results:
        st.warning("Run simulation first to export results")
        return

    results = st.session_state.results

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Download Options")

        # Text summary
        from hallar.visualization.reports import generate_text_summary
        summary = generate_text_summary(results)

        st.download_button(
            "📄 Download Text Summary",
            data=summary,
            file_name="hallar_summary.txt",
            mime="text/plain",
        )

        # JSON export
        import json
        json_data = json.dumps(results.to_dict(), indent=2, default=str)

        st.download_button(
            "📊 Download JSON Results",
            data=json_data,
            file_name="hallar_results.json",
            mime="application/json",
        )

        # CSV export
        data = []
        for r in results.ranked_results:
            data.append({
                "ID": r.scenario.id,
                "Name": r.scenario.name,
                "Utility": r.utility,
                "Expected_NPV": r.metrics["expected_npv"],
                "NPV_StdDev": r.metrics["npv_std"],
                "Prob_Loss": r.metrics["prob_loss"],
                "Expected_Time": r.metrics["expected_time"],
                "Quality_Score": r.metrics["quality_score"],
                "Affordability_Score": r.metrics["affordability_score"],
                "Passed_Constraints": r.passed_constraints,
            })
        df = pd.DataFrame(data)
        csv_data = df.to_csv(index=False)

        st.download_button(
            "📑 Download CSV Results",
            data=csv_data,
            file_name="hallar_results.csv",
            mime="text/csv",
        )

    with col2:
        st.subheader("Preview")

        preview_type = st.radio(
            "Preview",
            ["Text Summary", "Results Table"],
            horizontal=True,
        )

        if preview_type == "Text Summary":
            st.code(summary[:2000] + "\n..." if len(summary) > 2000 else summary, language=None)
        else:
            st.dataframe(df, hide_index=True)


if __name__ == "__main__":
    main()
