"""Chart generation for Hallar DSS."""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    from hallar.simulation.monte_carlo import FullAnalysisResults, ScenarioResult
    from hallar.analysis.sensitivity import SensitivityResult

# Try to import plotly, fall back to matplotlib
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def create_npv_distribution_chart(
    results: "FullAnalysisResults",
    scenario_ids: Optional[List[str]] = None,
    use_plotly: bool = True,
) -> Any:
    """
    Create NPV distribution histogram for scenarios.

    Args:
        results: Full analysis results
        scenario_ids: Specific scenarios to include (None = top 5)
        use_plotly: Use Plotly if available (else matplotlib)

    Returns:
        Plotly figure or matplotlib figure
    """
    if scenario_ids is None:
        # Default to top 5 by utility
        scenario_ids = [r.scenario.id for r in results.ranked_results[:5]]

    # Filter results
    selected = [r for r in results.scenario_results if r.scenario.id in scenario_ids]

    if use_plotly and PLOTLY_AVAILABLE:
        fig = go.Figure()

        colors = px.colors.qualitative.Set2

        for i, result in enumerate(selected):
            npv_data = result.simulation_results.npv

            fig.add_trace(go.Histogram(
                x=npv_data,
                name=f"{result.scenario.id}: {result.scenario.name[:20]}",
                opacity=0.6,
                marker_color=colors[i % len(colors)],
                nbinsx=50,
            ))

            # Add mean line
            mean_npv = np.mean(npv_data)
            fig.add_vline(
                x=mean_npv,
                line_dash="dash",
                line_color=colors[i % len(colors)],
                annotation_text=f"{result.scenario.id} mean",
            )

        # Add zero line (break-even)
        fig.add_vline(x=0, line_dash="solid", line_color="red", line_width=2)

        fig.update_layout(
            title="NPV Distribution by Scenario",
            xaxis_title="NPV (ISK millions)",
            yaxis_title="Frequency",
            barmode="overlay",
            legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
        )

        return fig

    elif MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(12, 6))

        colors = plt.cm.Set2.colors

        for i, result in enumerate(selected):
            npv_data = result.simulation_results.npv
            ax.hist(
                npv_data,
                bins=50,
                alpha=0.6,
                label=f"{result.scenario.id}: {result.scenario.name[:20]}",
                color=colors[i % len(colors)],
            )
            ax.axvline(np.mean(npv_data), linestyle="--", color=colors[i % len(colors)])

        ax.axvline(0, color="red", linewidth=2, label="Break-even")
        ax.set_xlabel("NPV (ISK millions)")
        ax.set_ylabel("Frequency")
        ax.set_title("NPV Distribution by Scenario")
        ax.legend()

        return fig

    else:
        raise ImportError("Neither plotly nor matplotlib available")


def create_scenario_comparison_radar(
    results: "FullAnalysisResults",
    scenario_ids: Optional[List[str]] = None,
    use_plotly: bool = True,
) -> Any:
    """
    Create radar chart comparing scenarios across objectives.

    Args:
        results: Full analysis results
        scenario_ids: Specific scenarios to include (None = top 3)
        use_plotly: Use Plotly if available

    Returns:
        Plotly figure or matplotlib figure
    """
    if scenario_ids is None:
        scenario_ids = [r.scenario.id for r in results.ranked_results[:3]]

    selected = [r for r in results.scenario_results if r.scenario.id in scenario_ids]

    objectives = ["Speed", "Affordability", "Quality", "Financial"]
    objective_keys = ["expected_time", "affordability_score", "quality_score", "expected_npv"]

    # Normalize values to 0-1 for radar chart
    all_values = {key: [] for key in objective_keys}
    for result in results.scenario_results:
        for key in objective_keys:
            all_values[key].append(result.metrics.get(key, 0))

    def normalize(value, key):
        vals = all_values[key]
        min_v, max_v = min(vals), max(vals)
        if max_v == min_v:
            return 0.5
        norm = (value - min_v) / (max_v - min_v)
        # Invert speed (lower is better)
        if key == "expected_time":
            norm = 1 - norm
        return norm

    if use_plotly and PLOTLY_AVAILABLE:
        fig = go.Figure()

        colors = px.colors.qualitative.Set2

        for i, result in enumerate(selected):
            values = [normalize(result.metrics.get(key, 0), key) for key in objective_keys]
            values.append(values[0])  # Close the polygon

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=objectives + [objectives[0]],
                fill="toself",
                name=f"{result.scenario.id}: {result.scenario.name[:20]}",
                opacity=0.6,
                line_color=colors[i % len(colors)],
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            title="Scenario Comparison (Radar Chart)",
            showlegend=True,
        )

        return fig

    elif MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection="polar"))

        angles = np.linspace(0, 2 * np.pi, len(objectives), endpoint=False).tolist()
        angles += angles[:1]  # Close the polygon

        colors = plt.cm.Set2.colors

        for i, result in enumerate(selected):
            values = [normalize(result.metrics.get(key, 0), key) for key in objective_keys]
            values += values[:1]

            ax.plot(angles, values, "o-", linewidth=2,
                    label=f"{result.scenario.id}", color=colors[i % len(colors)])
            ax.fill(angles, values, alpha=0.25, color=colors[i % len(colors)])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(objectives)
        ax.set_ylim(0, 1)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0))
        ax.set_title("Scenario Comparison")

        return fig

    else:
        raise ImportError("Neither plotly nor matplotlib available")


def create_sensitivity_tornado(
    sensitivity_results: List["SensitivityResult"],
    top_n: int = 10,
    use_plotly: bool = True,
) -> Any:
    """
    Create tornado diagram for sensitivity analysis.

    Args:
        sensitivity_results: Results from sensitivity_analysis
        top_n: Number of top parameters to show
        use_plotly: Use Plotly if available

    Returns:
        Plotly figure or matplotlib figure
    """
    # Take top N by swing
    top_results = sensitivity_results[:top_n]

    params = [r.parameter for r in top_results]
    low_impacts = [r.low_npv - r.base_npv for r in top_results]
    high_impacts = [r.high_npv - r.base_npv for r in top_results]

    if use_plotly and PLOTLY_AVAILABLE:
        fig = go.Figure()

        fig.add_trace(go.Bar(
            y=params,
            x=low_impacts,
            orientation="h",
            name="-20%",
            marker_color="steelblue",
        ))

        fig.add_trace(go.Bar(
            y=params,
            x=high_impacts,
            orientation="h",
            name="+20%",
            marker_color="coral",
        ))

        fig.update_layout(
            title="Sensitivity Analysis (Tornado Diagram)",
            xaxis_title="Change in NPV (ISK millions)",
            yaxis_title="Parameter",
            barmode="overlay",
            yaxis=dict(autorange="reversed"),
        )

        return fig

    elif MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(10, 6))

        y_pos = np.arange(len(params))

        ax.barh(y_pos - 0.2, low_impacts, height=0.4, label="-20%", color="steelblue")
        ax.barh(y_pos + 0.2, high_impacts, height=0.4, label="+20%", color="coral")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(params)
        ax.invert_yaxis()
        ax.set_xlabel("Change in NPV (ISK millions)")
        ax.set_title("Sensitivity Analysis (Tornado Diagram)")
        ax.legend()
        ax.axvline(0, color="black", linewidth=0.5)

        return fig

    else:
        raise ImportError("Neither plotly nor matplotlib available")


def create_pareto_frontier_plot(
    results: "FullAnalysisResults",
    x_objective: str = "expected_npv",
    y_objective: str = "expected_time",
    use_plotly: bool = True,
) -> Any:
    """
    Create 2D Pareto frontier plot.

    Args:
        results: Full analysis results
        x_objective: Metric for x-axis
        y_objective: Metric for y-axis
        use_plotly: Use Plotly if available

    Returns:
        Plotly figure or matplotlib figure
    """
    from hallar.analysis.dominance import find_pareto_frontier

    dominance = find_pareto_frontier(results)
    pareto_ids = {d.scenario_id for d in dominance if d.is_pareto_optimal}

    if use_plotly and PLOTLY_AVAILABLE:
        fig = go.Figure()

        # Non-Pareto points
        non_pareto = [r for r in results.scenario_results if r.scenario.id not in pareto_ids]
        pareto = [r for r in results.scenario_results if r.scenario.id in pareto_ids]

        if non_pareto:
            fig.add_trace(go.Scatter(
                x=[r.metrics[x_objective] for r in non_pareto],
                y=[r.metrics[y_objective] for r in non_pareto],
                mode="markers+text",
                marker=dict(size=10, color="gray", opacity=0.5),
                text=[r.scenario.id for r in non_pareto],
                textposition="top center",
                name="Dominated",
            ))

        if pareto:
            fig.add_trace(go.Scatter(
                x=[r.metrics[x_objective] for r in pareto],
                y=[r.metrics[y_objective] for r in pareto],
                mode="markers+text",
                marker=dict(size=15, color="green", symbol="star"),
                text=[r.scenario.id for r in pareto],
                textposition="top center",
                name="Pareto Optimal",
            ))

        fig.update_layout(
            title="Pareto Frontier",
            xaxis_title=x_objective.replace("_", " ").title(),
            yaxis_title=y_objective.replace("_", " ").title(),
        )

        return fig

    elif MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(10, 6))

        non_pareto = [r for r in results.scenario_results if r.scenario.id not in pareto_ids]
        pareto = [r for r in results.scenario_results if r.scenario.id in pareto_ids]

        if non_pareto:
            ax.scatter(
                [r.metrics[x_objective] for r in non_pareto],
                [r.metrics[y_objective] for r in non_pareto],
                c="gray", alpha=0.5, s=100, label="Dominated",
            )
            for r in non_pareto:
                ax.annotate(r.scenario.id, (r.metrics[x_objective], r.metrics[y_objective]))

        if pareto:
            ax.scatter(
                [r.metrics[x_objective] for r in pareto],
                [r.metrics[y_objective] for r in pareto],
                c="green", s=200, marker="*", label="Pareto Optimal",
            )
            for r in pareto:
                ax.annotate(r.scenario.id, (r.metrics[x_objective], r.metrics[y_objective]))

        ax.set_xlabel(x_objective.replace("_", " ").title())
        ax.set_ylabel(y_objective.replace("_", " ").title())
        ax.set_title("Pareto Frontier")
        ax.legend()

        return fig

    else:
        raise ImportError("Neither plotly nor matplotlib available")


def create_weight_sensitivity_heatmap(
    weight_sensitivity: Dict[str, Dict[str, float]],
    use_plotly: bool = True,
) -> Any:
    """
    Create heatmap showing utility scores under different weight profiles.

    Args:
        weight_sensitivity: Output from weight_sensitivity_analysis
        use_plotly: Use Plotly if available

    Returns:
        Plotly figure or matplotlib figure
    """
    if not weight_sensitivity:
        raise ValueError("No weight sensitivity data")

    # Build matrix
    profiles = list(weight_sensitivity.keys())
    scenarios = list(list(weight_sensitivity.values())[0].keys())

    matrix = np.zeros((len(scenarios), len(profiles)))
    for j, profile in enumerate(profiles):
        for i, scenario in enumerate(scenarios):
            matrix[i, j] = weight_sensitivity[profile].get(scenario, 0)

    if use_plotly and PLOTLY_AVAILABLE:
        fig = go.Figure(data=go.Heatmap(
            z=matrix,
            x=profiles,
            y=scenarios,
            colorscale="RdYlGn",
            text=np.round(matrix, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
        ))

        fig.update_layout(
            title="Utility by Weight Profile",
            xaxis_title="Weight Profile",
            yaxis_title="Scenario",
            xaxis=dict(tickangle=45),
        )

        return fig

    elif MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(12, 8))

        im = ax.imshow(matrix, cmap="RdYlGn", aspect="auto")

        ax.set_xticks(np.arange(len(profiles)))
        ax.set_yticks(np.arange(len(scenarios)))
        ax.set_xticklabels(profiles, rotation=45, ha="right")
        ax.set_yticklabels(scenarios)

        for i in range(len(scenarios)):
            for j in range(len(profiles)):
                ax.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center")

        ax.set_title("Utility by Weight Profile")
        fig.colorbar(im)

        return fig

    else:
        raise ImportError("Neither plotly nor matplotlib available")


def create_timeline_chart(
    results: "FullAnalysisResults",
    scenario_ids: Optional[List[str]] = None,
    use_plotly: bool = True,
) -> Any:
    """
    Create timeline comparison chart.

    Args:
        results: Full analysis results
        scenario_ids: Specific scenarios to include
        use_plotly: Use Plotly if available

    Returns:
        Plotly figure or matplotlib figure
    """
    if scenario_ids is None:
        scenario_ids = [r.scenario.id for r in results.ranked_results[:5]]

    selected = [r for r in results.scenario_results if r.scenario.id in scenario_ids]

    if use_plotly and PLOTLY_AVAILABLE:
        fig = go.Figure()

        for result in selected:
            sim = result.simulation_results

            fig.add_trace(go.Box(
                x=[result.scenario.id] * len(sim.sixty_percent_months),
                y=sim.sixty_percent_months,
                name=result.scenario.id,
                boxmean=True,
            ))

        fig.update_layout(
            title="Timeline Distribution (60% Completion)",
            xaxis_title="Scenario",
            yaxis_title="Months",
            showlegend=False,
        )

        return fig

    elif MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(10, 6))

        data = [r.simulation_results.sixty_percent_months for r in selected]
        labels = [r.scenario.id for r in selected]

        ax.boxplot(data, labels=labels, showmeans=True)
        ax.set_ylabel("Months")
        ax.set_title("Timeline Distribution (60% Completion)")

        return fig

    else:
        raise ImportError("Neither plotly nor matplotlib available")


def create_ranking_bar_chart(
    results: "FullAnalysisResults",
    use_plotly: bool = True,
) -> Any:
    """
    Create bar chart showing scenario rankings by utility.

    Args:
        results: Full analysis results
        use_plotly: Use Plotly if available

    Returns:
        Plotly figure or matplotlib figure
    """
    scenarios = [r.scenario.id for r in results.ranked_results]
    utilities = [r.utility for r in results.ranked_results]
    passed = [r.passed_constraints for r in results.ranked_results]

    colors = ["green" if p else "red" for p in passed]

    if use_plotly and PLOTLY_AVAILABLE:
        fig = go.Figure(data=[
            go.Bar(
                x=scenarios,
                y=utilities,
                marker_color=colors,
                text=[f"{u:.3f}" for u in utilities],
                textposition="auto",
            )
        ])

        fig.update_layout(
            title="Scenario Ranking by Utility Score",
            xaxis_title="Scenario",
            yaxis_title="Utility Score",
            yaxis=dict(range=[0, 1]),
        )

        return fig

    elif MATPLOTLIB_AVAILABLE:
        fig, ax = plt.subplots(figsize=(12, 6))

        bars = ax.bar(scenarios, utilities, color=colors)

        for bar, utility in zip(bars, utilities):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{utility:.3f}", ha="center", va="bottom")

        ax.set_ylabel("Utility Score")
        ax.set_title("Scenario Ranking by Utility Score")
        ax.set_ylim(0, 1)

        # Legend
        green_patch = mpatches.Patch(color="green", label="Passed Constraints")
        red_patch = mpatches.Patch(color="red", label="Failed Constraints")
        ax.legend(handles=[green_patch, red_patch])

        return fig

    else:
        raise ImportError("Neither plotly nor matplotlib available")
