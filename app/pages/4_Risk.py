"""Risk Analysis Page for Hallar DSS."""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Risk - Hallar DSS", page_icon="⚠️", layout="wide")

st.title("⚠️ Áhættugreining / Risk Analysis")
st.markdown("*Analyze counterparty and project risks for each scenario*")


def main():
    scenarios = st.session_state.get("composed_scenarios")
    risk_catalog = st.session_state.get("risk_catalog")
    counterparties = st.session_state.get("counterparty_profiles")

    if not scenarios:
        st.warning("Scenarios data not loaded. Please return to home page.")
        return

    # Sidebar - Scenario selection
    with st.sidebar:
        st.header("Select Scenario")

        scenario_options = list(scenarios.scenarios.keys())
        selected_scenario_id = st.selectbox(
            "Scenario",
            options=scenario_options,
            format_func=lambda x: f"{x}: {scenarios.scenarios[x].name}",
        )

        st.divider()

        st.header("Risk Settings")
        base_npv = st.number_input("Base NPV (M ISK)", value=5000, step=500)
        exposure = st.number_input("City Exposure (M ISK)", value=16500, step=500)

    selected_scenario = scenarios.scenarios[selected_scenario_id]

    # Scenario overview
    st.subheader(f"📋 {selected_scenario.id}: {selected_scenario.name}")
    st.caption(f"*{selected_scenario.name_is}*")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Counterparty", selected_scenario.counterparty)
    with col2:
        st.metric("Default Probability", f"{selected_scenario.get_default_probability_likely():.1%}")
    with col3:
        st.metric("City Control", f"{selected_scenario.city_control_score}%")
    with col4:
        st.metric("Risk Score", f"{selected_scenario.goal_scores.risk}")

    st.divider()

    # Counterparty Risk Analysis
    st.subheader("🏦 Counterparty Risk")

    if counterparties:
        profile = counterparties.get(selected_scenario.counterparty)

        if profile:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**{profile.name}** / *{profile.name_is}*")
                st.markdown(profile.description)

                st.markdown("**Risk Characteristics:**")
                st.markdown(f"- Category: {profile.category}")
                st.markdown(f"- Financial Strength: {profile.financial_strength}")
                st.markdown(f"- Track Record: {profile.track_record}")

                if profile.risk_factors:
                    st.markdown("**Risk Factors:**")
                    for factor in profile.risk_factors:
                        st.markdown(f"- {factor}")

            with col2:
                st.markdown("**Default Probability Distribution:**")
                default_prob = profile.default_probability
                prob_data = pd.DataFrame({
                    "Estimate": ["Minimum", "Most Likely", "Maximum"],
                    "Probability": [default_prob.min * 100, default_prob.likely * 100, default_prob.max * 100],
                })
                st.bar_chart(prob_data, x="Estimate", y="Probability", height=200)

                st.metric("Recovery Rate", f"{profile.recovery_rate:.0%}")

                # Calculate expected loss
                lgd = (1 - profile.recovery_rate) * exposure
                expected_loss = lgd * default_prob.likely
                st.metric("Expected Loss Given Default", f"{lgd:,.0f} M ISK")
                st.metric("Expected Loss (prob × LGD)", f"{expected_loss:,.0f} M ISK")
        else:
            st.info(f"No detailed profile for counterparty: {selected_scenario.counterparty}")
    else:
        st.warning("Counterparty profiles not loaded")

    st.divider()

    # Risk Catalog Analysis
    st.subheader("📊 Risk Catalog Analysis")

    if risk_catalog:
        from hallar.analysis import analyze_scenario_risks

        # Analyze risks
        if counterparties:
            risk_profile = analyze_scenario_risks(
                selected_scenario,
                risk_catalog,
                counterparties,
                base_npv=base_npv,
                exposure=exposure,
            )

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Risk Score", f"{risk_profile.risk_score:.0f}/100")
            with col2:
                st.metric("Risk Category", risk_profile.risk_category.upper())
            with col3:
                st.metric("Total Expected Loss", f"{risk_profile.total_expected_loss:,.0f} M ISK")
            with col4:
                st.metric("Active Risks", len(risk_profile.risk_assessments))

            # Risk breakdown table
            st.markdown("**Risk Assessment Details:**")

            risk_data = []
            for assessment in risk_profile.risk_assessments:
                risk_data.append({
                    "Risk": assessment.risk_name,
                    "Probability": f"{assessment.probability:.1%}",
                    "Impact": f"{assessment.expected_impact:,.0f} M ISK",
                    "Expected Loss": f"{assessment.expected_loss:,.0f} M ISK",
                    "Severity": assessment.severity.upper(),
                })

            if risk_data:
                st.dataframe(pd.DataFrame(risk_data), hide_index=True, use_container_width=True)
            else:
                st.info("No significant risks identified for this scenario")

        # Risk catalog browser
        st.markdown("**Browse Risk Catalog:**")

        categories = list(set(r.category for r in risk_catalog.risks.values()))
        selected_category = st.selectbox("Filter by Category", ["All"] + categories)

        for risk_id, risk in risk_catalog.risks.items():
            if selected_category != "All" and risk.category != selected_category:
                continue

            with st.expander(f"{risk_id}: {risk.name}"):
                st.markdown(f"**Description:** {risk.description}")
                st.markdown(f"**Category:** {risk.category}")

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Probability:**")
                    st.markdown(f"- Min: {risk.probability.min:.1%}")
                    st.markdown(f"- Likely: {risk.probability.likely:.1%}")
                    st.markdown(f"- Max: {risk.probability.max:.1%}")

                with col2:
                    if risk.mitigations:
                        st.markdown("**Mitigations:**")
                        for m in risk.mitigations:
                            st.markdown(f"- {m}")
    else:
        st.warning("Risk catalog not loaded")

    st.divider()

    # Scenario Comparison
    st.subheader("📈 Scenario Risk Comparison")

    if counterparties and risk_catalog:
        from hallar.analysis import compare_scenario_risks

        all_profiles = compare_scenario_risks(scenarios, risk_catalog, counterparties)

        comparison_data = []
        for profile in all_profiles:
            comparison_data.append({
                "Scenario": profile.scenario_id,
                "Name": profile.scenario_name[:25] + "...",
                "Risk Score": profile.risk_score,
                "Category": profile.risk_category,
                "Expected Loss": f"{profile.total_expected_loss:,.0f}",
                "Counterparty": profile.counterparty_risk.counterparty_type,
                "Default Prob": f"{profile.counterparty_risk.default_probability:.1%}",
            })

        df = pd.DataFrame(comparison_data)
        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Risk Score": st.column_config.ProgressColumn(min_value=0, max_value=100),
            }
        )


if __name__ == "__main__":
    main()
