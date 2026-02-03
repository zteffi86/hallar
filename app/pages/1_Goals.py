"""Goals Configuration Page for Hallar DSS."""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Goals - Hallar DSS", page_icon="⚖️", layout="wide")

st.title("⚖️ Markmið / Goals Configuration")
st.markdown("*Configure goal weights to reflect political priorities*")


def get_weights_from_session():
    """Get current weights from session state."""
    if st.session_state.get("custom_weights"):
        return st.session_state.custom_weights
    goals = st.session_state.get("goals")
    if goals and st.session_state.get("weight_preset") in goals.presets:
        return goals.presets[st.session_state.weight_preset].weights
    return {"G1": 0.167, "G2": 0.167, "G3": 0.167, "G4": 0.167, "G5": 0.167, "G6": 0.165}


def main():
    goals = st.session_state.get("goals")

    if not goals:
        st.warning("Goals data not loaded. Please return to home page.")
        return

    # Sidebar - Preset selection
    with st.sidebar:
        st.header("Weight Presets")

        preset_options = list(goals.presets.keys())
        preset_names = {pid: goals.presets[pid].name_en for pid in preset_options}

        selected_preset = st.selectbox(
            "Select Preset",
            options=preset_options,
            format_func=lambda x: preset_names.get(x, x),
            index=preset_options.index(st.session_state.get("weight_preset", "balanced")) if st.session_state.get("weight_preset", "balanced") in preset_options else 0,
        )

        if st.button("Apply Preset", use_container_width=True):
            st.session_state.weight_preset = selected_preset
            st.session_state.custom_weights = None
            st.rerun()

        st.divider()

        # Reset to balanced
        if st.button("Reset to Balanced", use_container_width=True):
            st.session_state.weight_preset = "balanced"
            st.session_state.custom_weights = None
            st.rerun()

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Goal Definitions")

        for goal_id, goal in goals.goals.items():
            with st.expander(f"{goal.icon} {goal.name} / {goal.name_en}", expanded=False):
                st.markdown(f"**Description (IS):** {goal.description}")
                st.markdown(f"**Description (EN):** {goal.description_en}")
                st.markdown(f"**Direction:** {'Maximize ↑' if goal.direction.value == 'maximize' else 'Minimize ↓'}")
                st.markdown(f"**Metrics:** {', '.join(goal.metrics)}")

    with col2:
        st.subheader("Current Weights")

        weights = get_weights_from_session()

        # Display weights as bar chart
        weight_data = []
        for goal_id, goal in goals.goals.items():
            weight_data.append({
                "Goal": f"{goal.icon} {goal.name_en}",
                "Weight": weights.get(goal_id, 0) * 100,
            })

        df = pd.DataFrame(weight_data)
        st.bar_chart(df, x="Goal", y="Weight", height=300)

    st.divider()

    # Custom weight sliders
    st.subheader("🎚️ Custom Weights")
    st.markdown("*Adjust weights using sliders. Weights will be normalized to sum to 100%.*")

    current_weights = get_weights_from_session()

    slider_cols = st.columns(3)
    new_weights = {}

    for i, (goal_id, goal) in enumerate(goals.goals.items()):
        with slider_cols[i % 3]:
            value = current_weights.get(goal_id, 0.167)
            new_weights[goal_id] = st.slider(
                f"{goal.icon} {goal.name_en}",
                min_value=0.0,
                max_value=1.0,
                value=value,
                step=0.05,
                key=f"weight_{goal_id}",
            )

    # Normalize and display
    total = sum(new_weights.values())
    if total > 0:
        normalized = {k: v / total for k, v in new_weights.items()}

        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Normalized weights:** " + ", ".join([
                f"{goals.goals[k].name_en}: {v:.0%}"
                for k, v in normalized.items()
            ]))

        with col2:
            if st.button("💾 Save Custom Weights", type="primary", use_container_width=True):
                st.session_state.custom_weights = normalized
                st.session_state.weight_preset = "custom"
                st.success("Custom weights saved!")

    st.divider()

    # Preset comparison table
    st.subheader("📊 Preset Comparison")

    preset_data = []
    for preset_id, preset in goals.presets.items():
        row = {"Preset": preset.name_en}
        for goal_id in goals.goals:
            row[goals.goals[goal_id].name_en] = f"{preset.weights.get(goal_id, 0):.0%}"
        preset_data.append(row)

    st.dataframe(pd.DataFrame(preset_data), hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()
