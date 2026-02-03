"""Scenario Explorer Page for Hallar DSS."""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Scenarios - Hallar DSS", page_icon="📊", layout="wide")

st.title("📊 Sviðsmyndir / Scenario Explorer")
st.markdown("*Browse and compare pre-defined development scenarios*")


def create_goal_radar_data(scenario):
    """Create data for radar chart."""
    return {
        "Speed": scenario.goal_scores.speed,
        "Affordability": scenario.goal_scores.affordability,
        "Quality": scenario.goal_scores.quality,
        "Financial": scenario.goal_scores.financial,
        "Risk": scenario.goal_scores.risk,
        "Control": scenario.goal_scores.control,
    }


def main():
    scenarios = st.session_state.get("composed_scenarios")

    if not scenarios:
        st.warning("Scenarios data not loaded. Please return to home page.")
        return

    # Sidebar - Filters
    with st.sidebar:
        st.header("Filters")

        # Counterparty filter
        counterparties = list(set(s.counterparty for s in scenarios.scenarios.values()))
        selected_counterparties = st.multiselect(
            "Counterparty Type",
            options=counterparties,
            default=counterparties,
        )

        # Control score filter
        min_control = st.slider("Minimum City Control", 0, 100, 0)

        # Risk filter
        max_risk = st.slider("Maximum Default Probability", 0.0, 0.20, 0.20, 0.01, format="%.1%%")

        st.divider()

        # Goal priority filter
        st.subheader("Sort by Goal")
        sort_goal = st.selectbox(
            "Primary Goal",
            options=["speed", "affordability", "quality", "financial", "risk", "control"],
            format_func=lambda x: x.capitalize(),
        )

    # Filter scenarios
    filtered = [
        s for s in scenarios.scenarios.values()
        if s.counterparty in selected_counterparties
        and s.city_control_score >= min_control
        and s.get_default_probability_likely() <= max_risk
    ]

    # Sort by selected goal
    filtered.sort(key=lambda s: getattr(s.goal_scores, sort_goal), reverse=True)

    # Summary metrics
    st.markdown(f"**Showing {len(filtered)} of {len(scenarios.scenarios)} scenarios**")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Filtered Scenarios", len(filtered))
    with col2:
        if filtered:
            avg_control = sum(s.city_control_score for s in filtered) / len(filtered)
            st.metric("Avg City Control", f"{avg_control:.0f}%")
    with col3:
        if filtered:
            avg_risk = sum(s.get_default_probability_likely() for s in filtered) / len(filtered)
            st.metric("Avg Default Risk", f"{avg_risk:.1%}")

    st.divider()

    # Scenario cards
    for scenario in filtered:
        with st.container():
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.subheader(f"{scenario.id}: {scenario.name}")
                st.caption(f"*{scenario.name_is}*")
                st.markdown(scenario.description)

                # Components
                st.markdown("**Components:**")
                comp = scenario.components
                st.markdown(f"- Ownership: `{comp.ownership}` | Financing: `{comp.financing}`")
                st.markdown(f"- Byggingarrétt: `{comp.byggingarrettur}` | Infrastructure: `{comp.infrastructure}`")

            with col2:
                # Goal scores as horizontal bars
                st.markdown("**Goal Scores:**")

                scores = create_goal_radar_data(scenario)
                df = pd.DataFrame({
                    "Goal": list(scores.keys()),
                    "Score": list(scores.values()),
                })
                st.bar_chart(df, x="Goal", y="Score", height=200)

            with col3:
                # Key metrics
                st.metric("City Control", f"{scenario.city_control_score}%")
                st.metric("Default Risk", f"{scenario.get_default_probability_likely():.1%}")
                st.metric("Counterparty", scenario.counterparty)

                # Affordability commitment
                if scenario.affordability_commitment:
                    st.metric("Affordability %", f"{scenario.affordability_commitment.minimum_pct:.0%}")

            st.divider()

    # Comparison table
    st.subheader("📋 Comparison Table")

    table_data = []
    for s in filtered:
        table_data.append({
            "ID": s.id,
            "Name": s.name[:30] + "..." if len(s.name) > 30 else s.name,
            "Counterparty": s.counterparty,
            "Control": s.city_control_score,
            "Default Risk": f"{s.get_default_probability_likely():.1%}",
            "Speed": s.goal_scores.speed,
            "Affordability": s.goal_scores.affordability,
            "Quality": s.goal_scores.quality,
            "Financial": s.goal_scores.financial,
            "Risk": s.goal_scores.risk,
        })

    if table_data:
        st.dataframe(
            pd.DataFrame(table_data),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Control": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "Speed": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "Affordability": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "Quality": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "Financial": st.column_config.ProgressColumn(min_value=0, max_value=100),
                "Risk": st.column_config.ProgressColumn(min_value=0, max_value=100),
            }
        )


if __name__ == "__main__":
    main()
