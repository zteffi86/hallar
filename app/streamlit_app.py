"""Hallar DSS - Main Streamlit Application."""

import streamlit as st
from pathlib import Path

# Set page config first
st.set_page_config(
    page_title="Hallar DSS",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        # Data
        "scenarios": None,
        "markets": None,
        "constraints": None,
        "weights": None,
        "results": None,
        # Expanded data
        "goals": None,
        "ownership_structures": None,
        "financing_models": None,
        "byggingarrettur_options": None,
        "infrastructure_models": None,
        "counterparty_profiles": None,
        "composed_scenarios": None,
        "risk_catalog": None,
        "hallar_params": None,
        # Settings
        "weight_preset": "balanced",
        "custom_weights": None,
        "n_simulations": 10000,
        "random_seed": 42,
        "language": "is",  # Icelandic default
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_all_data():
    """Load all YAML data files."""
    import yaml

    data_dir = Path(__file__).parent.parent / "data"

    # Load goals
    if st.session_state.goals is None:
        try:
            with open(data_dir / "goals.yaml") as f:
                from hallar.models import GoalSet
                st.session_state.goals = GoalSet.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load hallar parameters
    if st.session_state.hallar_params is None:
        try:
            with open(data_dir / "hallar_parameters.yaml") as f:
                from hallar.models import HallarParameters
                st.session_state.hallar_params = HallarParameters.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load composed scenarios
    if st.session_state.composed_scenarios is None:
        try:
            with open(data_dir / "composed_scenarios.yaml") as f:
                from hallar.models import ComposedScenarioSet
                st.session_state.composed_scenarios = ComposedScenarioSet.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load ownership structures
    if st.session_state.ownership_structures is None:
        try:
            with open(data_dir / "ownership_structures.yaml") as f:
                from hallar.models import OwnershipSet
                st.session_state.ownership_structures = OwnershipSet.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load financing models
    if st.session_state.financing_models is None:
        try:
            with open(data_dir / "financing_models.yaml") as f:
                from hallar.models import FinancingSet
                st.session_state.financing_models = FinancingSet.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load byggingarrétt options
    if st.session_state.byggingarrettur_options is None:
        try:
            with open(data_dir / "byggingarrettur_options.yaml") as f:
                from hallar.models import ByggingarretturSet
                st.session_state.byggingarrettur_options = ByggingarretturSet.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load infrastructure models
    if st.session_state.infrastructure_models is None:
        try:
            with open(data_dir / "infrastructure_models.yaml") as f:
                from hallar.models import InfrastructureSet
                st.session_state.infrastructure_models = InfrastructureSet.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load counterparty profiles
    if st.session_state.counterparty_profiles is None:
        try:
            with open(data_dir / "counterparty_profiles.yaml") as f:
                from hallar.models import CounterpartySet
                st.session_state.counterparty_profiles = CounterpartySet.from_dict(yaml.safe_load(f))
        except Exception:
            pass

    # Load risk catalog
    if st.session_state.risk_catalog is None:
        try:
            with open(data_dir / "risks.yaml") as f:
                from hallar.models import RiskCatalog
                st.session_state.risk_catalog = RiskCatalog.from_dict(yaml.safe_load(f))
        except Exception:
            pass


def main():
    """Main application entry point."""
    initialize_session_state()
    load_all_data()

    # Header
    st.title("🏗️ Hallar Decision Support System")
    st.markdown("*Ákvarðanastuðningskerfi fyrir landþróun / Land Development Decision Support*")

    st.divider()

    # Overview cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        params = st.session_state.hallar_params
        if params:
            st.metric("Heildarflatarmál / Total Area", f"{params.units.total_units:,} units")
        else:
            st.metric("Heildarflatarmál / Total Area", "3,200 units")

    with col2:
        if params:
            st.metric("Byggingarrétt / Dev Rights", f"{params.byggingarrettur_valuation.total_value.likely:,.0f} M ISK")
        else:
            st.metric("Byggingarrétt / Dev Rights", "16,500 M ISK")

    with col3:
        if params:
            st.metric("Innviðakostnaður / Infrastructure", f"{params.infrastructure_costs.total.likely:,.0f} M ISK")
        else:
            st.metric("Innviðakostnaður / Infrastructure", "8,000 M ISK")

    with col4:
        scenarios = st.session_state.composed_scenarios
        if scenarios:
            st.metric("Sviðsmyndir / Scenarios", len(scenarios.scenarios))
        else:
            st.metric("Sviðsmyndir / Scenarios", "10")

    st.divider()

    # Navigation
    st.header("📍 Leiðsögn / Navigation")

    nav_col1, nav_col2, nav_col3 = st.columns(3)

    with nav_col1:
        st.subheader("🎯 Markmið / Goals")
        st.markdown("""
        Configure goal weights to reflect political priorities:
        - Speed (Hraði)
        - Affordability (Húsnæðisöryggi)
        - Quality (Gæði)
        - Financial (Fjárhagur)
        - Risk Management (Áhættustýring)
        - Control (Stjórn)
        """)
        st.page_link("pages/1_Goals.py", label="⚖️ Configure Goals", use_container_width=True)

    with nav_col2:
        st.subheader("📊 Sviðsmyndir / Scenarios")
        st.markdown("""
        Explore and compare development scenarios:
        - Browse pre-defined scenarios
        - View goal scores and risk profiles
        - Compare scenarios side-by-side
        """)
        st.page_link("pages/2_Scenarios.py", label="🔍 Explore Scenarios", use_container_width=True)

    with nav_col3:
        st.subheader("🔧 Samsetning / Composer")
        st.markdown("""
        Build custom scenarios from components:
        - Ownership structures (O1-O8)
        - Financing models (F1-F8)
        - Byggingarrétt options (B1-B6)
        - Infrastructure models (I1-I6)
        """)
        st.page_link("pages/3_Composer.py", label="🛠️ Build Scenario", use_container_width=True)

    st.divider()

    nav_col4, nav_col5, nav_col6 = st.columns(3)

    with nav_col4:
        st.subheader("⚠️ Áhættugreining / Risk Analysis")
        st.markdown("""
        Analyze risks for each scenario:
        - Counterparty risk profiles
        - Construction and market risks
        - VaR and CVaR calculations
        """)
        st.page_link("pages/4_Risk.py", label="📉 Analyze Risk", use_container_width=True)

    with nav_col5:
        st.subheader("🔬 Hermun / Simulation")
        st.markdown("""
        Run Monte Carlo simulations:
        - Probabilistic NPV analysis
        - Timeline uncertainty
        - Constraint checking
        """)
        st.page_link("pages/5_Simulation.py", label="▶️ Run Simulation", use_container_width=True)

    with nav_col6:
        st.subheader("📈 Samanburður / Comparison")
        st.markdown("""
        Compare and export results:
        - Side-by-side comparison
        - Pareto frontier analysis
        - Export reports
        """)
        st.page_link("pages/6_Comparison.py", label="📊 Compare Results", use_container_width=True)

    # Footer
    st.divider()
    st.markdown("""
    ---
    **Hallar DSS** | Ákvarðanastuðningskerfi fyrir landþróun í Reykjavík

    *This system helps evaluate land development scenarios by combining:*
    - Monte Carlo simulation for uncertainty quantification
    - Multi-objective optimization for goal balancing
    - Risk analysis for counterparty and project risks
    - Constraint checking for policy compliance
    """)


if __name__ == "__main__":
    main()
