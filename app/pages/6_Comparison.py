"""Comparison and Export Page for Hallar DSS."""

import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Comparison - Hallar DSS", page_icon="📈", layout="wide")

st.title("📈 Samanburður / Comparison & Export")
st.markdown("*Compare scenarios and export results*")


def main():
    scenarios = st.session_state.get("composed_scenarios")
    results = st.session_state.get("results")

    # Tab selection
    tab1, tab2, tab3 = st.tabs(["🔍 Compare Scenarios", "📊 Analysis Charts", "📥 Export"])

    with tab1:
        render_comparison_tab(scenarios)

    with tab2:
        render_analysis_tab(results)

    with tab3:
        render_export_tab(scenarios, results)


def render_comparison_tab(scenarios):
    """Render scenario comparison tab."""
    st.subheader("Select Scenarios to Compare")

    if not scenarios:
        st.warning("No scenarios loaded")
        return

    # Scenario selection
    scenario_ids = list(scenarios.scenarios.keys())
    selected_ids = st.multiselect(
        "Choose scenarios",
        options=scenario_ids,
        default=scenario_ids[:3] if len(scenario_ids) >= 3 else scenario_ids,
        max_selections=5,
    )

    if not selected_ids:
        st.info("Select scenarios to compare")
        return

    # Comparison table
    st.subheader("📋 Side-by-Side Comparison")

    comparison_data = []
    for sid in selected_ids:
        s = scenarios.scenarios[sid]
        comparison_data.append({
            "Attribute": "Name",
            sid: s.name,
        })
    # Transpose to have scenarios as columns
    attributes = [
        ("Name", lambda s: s.name),
        ("Icelandic Name", lambda s: s.name_is),
        ("Counterparty", lambda s: s.counterparty),
        ("City Control", lambda s: f"{s.city_control_score}%"),
        ("Default Prob", lambda s: f"{s.get_default_probability_likely():.1%}"),
        ("Speed Score", lambda s: s.goal_scores.speed),
        ("Affordability Score", lambda s: s.goal_scores.affordability),
        ("Quality Score", lambda s: s.goal_scores.quality),
        ("Financial Score", lambda s: s.goal_scores.financial),
        ("Risk Score", lambda s: s.goal_scores.risk),
        ("Control Score", lambda s: s.goal_scores.control),
        ("Ownership", lambda s: s.components.ownership),
        ("Financing", lambda s: s.components.financing),
        ("Byggingarrétt", lambda s: s.components.byggingarrettur),
        ("Infrastructure", lambda s: s.components.infrastructure),
    ]

    table_data = []
    for attr_name, attr_func in attributes:
        row = {"Attribute": attr_name}
        for sid in selected_ids:
            s = scenarios.scenarios[sid]
            row[sid] = attr_func(s)
        table_data.append(row)

    st.dataframe(pd.DataFrame(table_data), hide_index=True, use_container_width=True)

    # Goal score comparison chart
    st.subheader("📊 Goal Score Comparison")

    chart_data = []
    for sid in selected_ids:
        s = scenarios.scenarios[sid]
        for goal, score in [
            ("Speed", s.goal_scores.speed),
            ("Affordability", s.goal_scores.affordability),
            ("Quality", s.goal_scores.quality),
            ("Financial", s.goal_scores.financial),
            ("Risk", s.goal_scores.risk),
            ("Control", s.goal_scores.control),
        ]:
            chart_data.append({
                "Scenario": sid,
                "Goal": goal,
                "Score": score,
            })

    df = pd.DataFrame(chart_data)

    # Create grouped bar chart
    pivot_df = df.pivot(index="Goal", columns="Scenario", values="Score")
    st.bar_chart(pivot_df, height=400)


def render_analysis_tab(results):
    """Render analysis charts tab."""
    st.subheader("📊 Analysis Visualizations")

    if not results:
        st.warning("No simulation results available. Run simulation first.")
        return

    chart_type = st.selectbox(
        "Select Chart Type",
        ["Utility Ranking", "NPV Distribution", "Risk vs Return", "Timeline Analysis"],
    )

    if chart_type == "Utility Ranking":
        st.markdown("**Scenario Utility Rankings**")

        chart_data = []
        for i, r in enumerate(results.ranked_results[:10], 1):
            chart_data.append({
                "Scenario": r.scenario.id,
                "Utility": r.utility,
            })

        df = pd.DataFrame(chart_data)
        st.bar_chart(df, x="Scenario", y="Utility", height=400)

    elif chart_type == "NPV Distribution":
        st.markdown("**NPV Distribution by Scenario**")

        npv_data = []
        for r in results.ranked_results[:5]:
            npv_data.append({
                "Scenario": r.scenario.id,
                "E[NPV]": r.metrics["expected_npv"],
                "Std Dev": r.metrics["npv_std"],
            })

        df = pd.DataFrame(npv_data)
        st.dataframe(df, hide_index=True)

        # Error bar chart approximation
        st.bar_chart(df, x="Scenario", y="E[NPV]", height=300)
        st.caption("Note: Standard deviations shown in table above")

    elif chart_type == "Risk vs Return":
        st.markdown("**Risk-Return Scatter**")

        scatter_data = []
        for r in results.ranked_results:
            scatter_data.append({
                "Scenario": r.scenario.id,
                "Expected NPV": r.metrics["expected_npv"],
                "P(Loss)": r.metrics["prob_loss"] * 100,
            })

        df = pd.DataFrame(scatter_data)
        st.scatter_chart(df, x="Expected NPV", y="P(Loss)", height=400)

    elif chart_type == "Timeline Analysis":
        st.markdown("**Timeline Distribution**")

        time_data = []
        for r in results.ranked_results[:5]:
            time_data.append({
                "Scenario": r.scenario.id,
                "Expected Time (months)": r.metrics["expected_time"],
            })

        df = pd.DataFrame(time_data)
        st.bar_chart(df, x="Scenario", y="Expected Time (months)", height=300)


def render_export_tab(scenarios, results):
    """Render export tab."""
    st.subheader("📥 Export Options")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Scenario Data**")

        if scenarios:
            # Export scenarios as JSON
            scenario_export = {
                sid: s.to_dict() for sid, s in scenarios.scenarios.items()
            }
            json_data = json.dumps(scenario_export, indent=2, default=str)

            st.download_button(
                "📊 Download Scenarios (JSON)",
                data=json_data,
                file_name="hallar_scenarios.json",
                mime="application/json",
            )

            # Export as CSV
            csv_data = []
            for sid, s in scenarios.scenarios.items():
                csv_data.append({
                    "ID": sid,
                    "Name": s.name,
                    "Counterparty": s.counterparty,
                    "City Control": s.city_control_score,
                    "Default Prob": s.get_default_probability_likely(),
                    "Speed": s.goal_scores.speed,
                    "Affordability": s.goal_scores.affordability,
                    "Quality": s.goal_scores.quality,
                    "Financial": s.goal_scores.financial,
                    "Risk": s.goal_scores.risk,
                    "Control": s.goal_scores.control,
                })

            df = pd.DataFrame(csv_data)
            csv_str = df.to_csv(index=False)

            st.download_button(
                "📑 Download Scenarios (CSV)",
                data=csv_str,
                file_name="hallar_scenarios.csv",
                mime="text/csv",
            )
        else:
            st.info("No scenario data to export")

    with col2:
        st.markdown("**Simulation Results**")

        if results:
            # Export results as JSON
            try:
                results_json = json.dumps(results.to_dict(), indent=2, default=str)
                st.download_button(
                    "📊 Download Results (JSON)",
                    data=results_json,
                    file_name="hallar_results.json",
                    mime="application/json",
                )
            except Exception as e:
                st.error(f"Error exporting JSON: {e}")

            # Export as CSV
            csv_data = []
            for i, r in enumerate(results.ranked_results, 1):
                csv_data.append({
                    "Rank": i,
                    "ID": r.scenario.id,
                    "Name": r.scenario.name,
                    "Utility": r.utility,
                    "Expected_NPV": r.metrics["expected_npv"],
                    "NPV_StdDev": r.metrics["npv_std"],
                    "Prob_Loss": r.metrics["prob_loss"],
                    "Expected_Time": r.metrics["expected_time"],
                    "Passed_Constraints": r.passed_constraints,
                })

            df = pd.DataFrame(csv_data)
            csv_str = df.to_csv(index=False)

            st.download_button(
                "📑 Download Results (CSV)",
                data=csv_str,
                file_name="hallar_results.csv",
                mime="text/csv",
            )

            # Text summary
            from hallar.visualization.reports import generate_text_summary
            try:
                summary = generate_text_summary(results)
                st.download_button(
                    "📄 Download Summary (TXT)",
                    data=summary,
                    file_name="hallar_summary.txt",
                    mime="text/plain",
                )
            except Exception as e:
                st.error(f"Error generating summary: {e}")
        else:
            st.info("No simulation results to export. Run simulation first.")

    st.divider()

    # Preview section
    st.subheader("👁️ Preview")

    preview_type = st.radio("Preview Type", ["Scenarios", "Results"], horizontal=True)

    if preview_type == "Scenarios" and scenarios:
        st.json({sid: s.to_dict() for sid, s in list(scenarios.scenarios.items())[:3]})
    elif preview_type == "Results" and results:
        preview_data = []
        for r in results.ranked_results[:5]:
            preview_data.append({
                "ID": r.scenario.id,
                "Utility": r.utility,
                "E[NPV]": r.metrics["expected_npv"],
            })
        st.dataframe(pd.DataFrame(preview_data), hide_index=True)
    else:
        st.info("No data to preview")


if __name__ == "__main__":
    main()
