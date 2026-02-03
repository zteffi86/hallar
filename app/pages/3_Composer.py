"""Structure Composer Page for Hallar DSS."""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Composer - Hallar DSS", page_icon="🔧", layout="wide")

st.title("🔧 Samsetning / Structure Composer")
st.markdown("*Build custom scenarios from component building blocks*")


def main():
    ownership = st.session_state.get("ownership_structures")
    financing = st.session_state.get("financing_models")
    byggingarrettur = st.session_state.get("byggingarrettur_options")
    infrastructure = st.session_state.get("infrastructure_models")
    counterparties = st.session_state.get("counterparty_profiles")

    if not all([ownership, financing, byggingarrettur, infrastructure]):
        st.warning("Component data not fully loaded. Please return to home page.")
        return

    # Component selection
    st.subheader("1️⃣ Select Components")

    col1, col2 = st.columns(2)

    with col1:
        # Ownership
        st.markdown("**Ownership Structure**")
        ownership_options = list(ownership.structures.keys())
        selected_ownership_id = st.selectbox(
            "Select ownership model",
            options=ownership_options,
            format_func=lambda x: f"{x}: {ownership.structures[x].name}",
            key="composer_ownership",
        )
        selected_ownership = ownership.structures[selected_ownership_id]

        with st.expander("View details"):
            st.markdown(f"**{selected_ownership.name}** / *{selected_ownership.name_is}*")
            st.markdown(selected_ownership.description)
            st.markdown(f"- City Role: {selected_ownership.city_role}")
            st.markdown(f"- Counterparty: {selected_ownership.counterparty}")
            st.markdown(f"- City Control: {selected_ownership.city_control}%")

        # Financing
        st.markdown("**Financing Model**")
        financing_options = list(financing.models.keys())
        selected_financing_id = st.selectbox(
            "Select financing model",
            options=financing_options,
            format_func=lambda x: f"{x}: {financing.models[x].name}",
            key="composer_financing",
        )
        selected_financing = financing.models[selected_financing_id]

        with st.expander("View details"):
            st.markdown(f"**{selected_financing.name}** / *{selected_financing.name_is}*")
            st.markdown(selected_financing.description)
            st.markdown(f"- Sources: {', '.join(selected_financing.sources)}")
            st.markdown(f"- City Cash Requirement: {selected_financing.city_cash_requirement}")

    with col2:
        # Byggingarrétt
        st.markdown("**Byggingarrétt Disposition**")
        bygg_options = list(byggingarrettur.options.keys())
        selected_bygg_id = st.selectbox(
            "Select byggingarrétt option",
            options=bygg_options,
            format_func=lambda x: f"{x}: {byggingarrettur.options[x].name}",
            key="composer_bygg",
        )
        selected_bygg = byggingarrettur.options[selected_bygg_id]

        with st.expander("View details"):
            st.markdown(f"**{selected_bygg.name}** / *{selected_bygg.name_is}*")
            st.markdown(selected_bygg.description)
            st.markdown(f"- Pricing Method: {selected_bygg.pricing.method}")
            st.markdown(f"- City Receives: {selected_bygg.city_receives.type}")

        # Infrastructure
        st.markdown("**Infrastructure Model**")
        infra_options = list(infrastructure.models.keys())
        selected_infra_id = st.selectbox(
            "Select infrastructure model",
            options=infra_options,
            format_func=lambda x: f"{x}: {infrastructure.models[x].name}",
            key="composer_infra",
        )
        selected_infra = infrastructure.models[selected_infra_id]

        with st.expander("View details"):
            st.markdown(f"**{selected_infra.name}** / *{selected_infra.name_is}*")
            st.markdown(selected_infra.description)
            st.markdown(f"- Delivery By: {selected_infra.delivery_by}")
            st.markdown(f"- Timing: {selected_infra.timing}")

    st.divider()

    # Validation
    st.subheader("2️⃣ Validate Composition")

    from hallar.analysis import validate_composition, estimate_goal_scores

    validation = validate_composition(
        selected_ownership,
        selected_financing,
        selected_bygg,
        selected_infra,
    )

    if validation.is_valid:
        st.success("✅ Valid composition - all components are compatible")
    else:
        st.error("❌ Invalid composition - incompatible components")
        for issue in validation.issues:
            st.markdown(f"- **{issue.severity.upper()}**: {issue.reason}")

    if validation.warnings:
        for warning in validation.warnings:
            st.warning(f"⚠️ {warning}")

    st.divider()

    # Estimated scores
    st.subheader("3️⃣ Estimated Goal Scores")

    counterparty_profile = None
    if counterparties and selected_ownership.counterparty:
        counterparty_profile = counterparties.get(selected_ownership.counterparty)

    estimated_scores = estimate_goal_scores(
        selected_ownership,
        selected_financing,
        selected_bygg,
        selected_infra,
        counterparty_profile,
    )

    col1, col2 = st.columns(2)

    with col1:
        score_data = {
            "Goal": ["Speed", "Affordability", "Quality", "Financial", "Risk", "Control"],
            "Score": [
                estimated_scores.speed,
                estimated_scores.affordability,
                estimated_scores.quality,
                estimated_scores.financial,
                estimated_scores.risk,
                estimated_scores.control,
            ],
        }
        st.bar_chart(pd.DataFrame(score_data), x="Goal", y="Score", height=300)

    with col2:
        st.metric("Speed", estimated_scores.speed)
        st.metric("Affordability", estimated_scores.affordability)
        st.metric("Quality", estimated_scores.quality)
        st.metric("Financial", estimated_scores.financial)
        st.metric("Risk", estimated_scores.risk)
        st.metric("Control", estimated_scores.control)

    st.divider()

    # Save composition
    st.subheader("4️⃣ Save Composition")

    scenario_name = st.text_input(
        "Scenario Name",
        value=f"Custom: {selected_ownership.name} + {selected_financing.name}",
    )

    if st.button("💾 Save Custom Scenario", type="primary", disabled=not validation.is_valid):
        from hallar.analysis import compose_scenario

        scenario, _ = compose_scenario(
            selected_ownership,
            selected_financing,
            selected_bygg,
            selected_infra,
            counterparty_profile,
        )

        if scenario:
            if "custom_scenarios" not in st.session_state:
                st.session_state.custom_scenarios = []
            st.session_state.custom_scenarios.append(scenario)
            st.success(f"Saved custom scenario: {scenario_name}")
        else:
            st.error("Failed to save scenario")

    # Show saved custom scenarios
    if st.session_state.get("custom_scenarios"):
        st.divider()
        st.subheader("📋 Saved Custom Scenarios")

        for i, cs in enumerate(st.session_state.custom_scenarios):
            with st.expander(f"{cs.id}: {cs.name}"):
                st.json({
                    "components": cs.components.to_dict(),
                    "counterparty": cs.counterparty,
                    "city_control": cs.city_control_score,
                    "goal_scores": cs.goal_scores.to_dict(),
                })


if __name__ == "__main__":
    main()
