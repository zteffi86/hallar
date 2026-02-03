"""Report generation for Hallar DSS."""

from typing import TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from hallar.simulation.monte_carlo import FullAnalysisResults


def generate_text_summary(results: "FullAnalysisResults") -> str:
    """
    Generate text summary of analysis results.

    Args:
        results: Full analysis results

    Returns:
        Formatted text summary
    """
    lines = []

    # Header
    lines.append("=" * 74)
    lines.append("                    HALLAR DECISION SUPPORT SYSTEM")
    lines.append("                         Results Summary")
    lines.append("=" * 74)
    lines.append(f" Simulation: {results.n_simulations:,} iterations | Weight Profile: {results.weight_profile.name}")
    lines.append(f" Date: {datetime.now().strftime('%Y-%m-%d')} | Scenarios: {len(results.scenario_results)} | Passed: {len(results.passed_scenarios)}")
    lines.append("=" * 74)
    lines.append("")

    # Top scenarios
    lines.append("-" * 74)
    lines.append(" TOP 3 SCENARIOS (by utility score)")
    lines.append("-" * 74)

    for i, result in enumerate(results.top_3, 1):
        lines.append(f" #{i}: {result.scenario.id} - {result.scenario.name}")
        lines.append(f"     Utility: {result.utility:.3f} | E[NPV]: {result.metrics['expected_npv']:,.0f}M | P(loss): {result.metrics['prob_loss']:.1%} | Time: {result.metrics['expected_time']:.0f} months")

        if result.passed_constraints:
            lines.append("     Status: All constraints passed")
        else:
            lines.append("     Status: FAILED constraints:")
            for vid, vmsg in result.constraint_violations[:3]:
                lines.append(f"       - {vmsg}")

        lines.append("")

    # Constraint summary
    lines.append("-" * 74)
    lines.append(" CONSTRAINT SUMMARY")
    lines.append("-" * 74)

    passed = [r for r in results.scenario_results if r.passed_constraints]
    failed = [r for r in results.scenario_results if not r.passed_constraints]

    lines.append(f" Passed ({len(passed)}): {', '.join(r.scenario.id for r in passed) or 'None'}")
    lines.append(f" Failed ({len(failed)}): {', '.join(r.scenario.id for r in failed) or 'None'}")
    lines.append("")

    # Eliminated scenarios details
    if failed:
        lines.append("-" * 74)
        lines.append(" ELIMINATED SCENARIOS")
        lines.append("-" * 74)

        for result in failed:
            lines.append(f" {result.scenario.id}: {result.scenario.name}")
            for vid, vmsg in result.constraint_violations:
                lines.append(f"   - {vmsg}")
            lines.append("")

    # Full ranking
    lines.append("-" * 74)
    lines.append(" FULL RANKING")
    lines.append("-" * 74)
    lines.append(f" {'Rank':<5} {'ID':<6} {'Utility':<10} {'E[NPV]':<12} {'P(loss)':<10} {'Time':<8} {'Status':<8}")
    lines.append("-" * 74)

    for i, result in enumerate(results.ranked_results, 1):
        status = "PASS" if result.passed_constraints else "FAIL"
        lines.append(
            f" {i:<5} {result.scenario.id:<6} {result.utility:<10.3f} "
            f"{result.metrics['expected_npv']:<12,.0f} {result.metrics['prob_loss']:<10.1%} "
            f"{result.metrics['expected_time']:<8.0f} {status:<8}"
        )

    lines.append("-" * 74)
    lines.append("")

    # Weight profile info
    lines.append("-" * 74)
    lines.append(" WEIGHT PROFILE: " + results.weight_profile.name)
    lines.append("-" * 74)
    for obj, weight in results.weight_profile.weights.items():
        lines.append(f"   {obj.capitalize():<15}: {weight:.0%}")
    lines.append("")

    return "\n".join(lines)


def generate_summary_report(
    results: "FullAnalysisResults",
    output_path: str,
    include_charts: bool = True,
) -> None:
    """
    Generate comprehensive summary report as HTML.

    Args:
        results: Full analysis results
        output_path: Path to output HTML file
        include_charts: Whether to include embedded charts
    """
    from hallar.visualization.charts import (
        create_ranking_bar_chart,
        create_scenario_comparison_radar,
        create_npv_distribution_chart,
    )

    html_parts = []

    # HTML header
    html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <title>Hallar DSS Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { color: #34495e; margin-top: 30px; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        .pass { color: #27ae60; font-weight: bold; }
        .fail { color: #e74c3c; font-weight: bold; }
        .metric-card { display: inline-block; background: #ecf0f1; padding: 15px 25px; margin: 10px; border-radius: 5px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .metric-label { font-size: 12px; color: #7f8c8d; }
        .scenario-box { border: 1px solid #ddd; padding: 20px; margin: 15px 0; border-radius: 5px; }
        .scenario-box.rank-1 { border-left: 5px solid gold; }
        .scenario-box.rank-2 { border-left: 5px solid silver; }
        .scenario-box.rank-3 { border-left: 5px solid #cd7f32; }
        .chart-container { margin: 20px 0; }
    </style>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
<div class="container">
""")

    # Title
    html_parts.append(f"""
    <h1>Hallar Decision Support System</h1>
    <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <p><strong>Simulations:</strong> {results.n_simulations:,} |
       <strong>Weight Profile:</strong> {results.weight_profile.name} |
       <strong>Random Seed:</strong> {results.random_seed}</p>
""")

    # Summary metrics
    passed = len(results.passed_scenarios)
    total = len(results.scenario_results)
    top_scenario = results.ranked_results[0] if results.ranked_results else None

    html_parts.append("""
    <h2>Executive Summary</h2>
    <div class="metric-cards">
""")

    html_parts.append(f"""
        <div class="metric-card">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Scenarios Evaluated</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{passed}</div>
            <div class="metric-label">Passed Constraints</div>
        </div>
""")

    if top_scenario:
        html_parts.append(f"""
        <div class="metric-card">
            <div class="metric-value">{top_scenario.scenario.id}</div>
            <div class="metric-label">Top Scenario</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{top_scenario.utility:.3f}</div>
            <div class="metric-label">Top Utility Score</div>
        </div>
""")

    html_parts.append("    </div>")

    # Top 3 scenarios
    html_parts.append("""
    <h2>Top Scenarios</h2>
""")

    for i, result in enumerate(results.top_3, 1):
        status_class = "pass" if result.passed_constraints else "fail"
        status_text = "All constraints passed" if result.passed_constraints else f"Failed {len(result.constraint_violations)} constraint(s)"

        html_parts.append(f"""
    <div class="scenario-box rank-{i}">
        <h3>#{i}: {result.scenario.id} - {result.scenario.name}</h3>
        <p>{result.scenario.description}</p>
        <table>
            <tr>
                <th>Utility</th>
                <th>E[NPV]</th>
                <th>P(Loss)</th>
                <th>Time (months)</th>
                <th>Quality</th>
                <th>Affordability</th>
            </tr>
            <tr>
                <td>{result.utility:.3f}</td>
                <td>{result.metrics['expected_npv']:,.0f} M</td>
                <td>{result.metrics['prob_loss']:.1%}</td>
                <td>{result.metrics['expected_time']:.0f}</td>
                <td>{result.metrics['quality_score']:.1f}</td>
                <td>{result.metrics['affordability_score']:.1f}</td>
            </tr>
        </table>
        <p class="{status_class}">{status_text}</p>
    </div>
""")

    # Full results table
    html_parts.append("""
    <h2>Full Results</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>ID</th>
            <th>Name</th>
            <th>Utility</th>
            <th>E[NPV]</th>
            <th>NPV Std</th>
            <th>P(Loss)</th>
            <th>Time</th>
            <th>Status</th>
        </tr>
""")

    for i, result in enumerate(results.ranked_results, 1):
        status_class = "pass" if result.passed_constraints else "fail"
        status_text = "PASS" if result.passed_constraints else "FAIL"

        html_parts.append(f"""
        <tr>
            <td>{i}</td>
            <td>{result.scenario.id}</td>
            <td>{result.scenario.name[:30]}...</td>
            <td>{result.utility:.3f}</td>
            <td>{result.metrics['expected_npv']:,.0f}</td>
            <td>{result.metrics['npv_std']:,.0f}</td>
            <td>{result.metrics['prob_loss']:.1%}</td>
            <td>{result.metrics['expected_time']:.0f}</td>
            <td class="{status_class}">{status_text}</td>
        </tr>
""")

    html_parts.append("    </table>")

    # Charts
    if include_charts:
        html_parts.append("""
    <h2>Visualizations</h2>
""")

        try:
            # Ranking chart
            fig = create_ranking_bar_chart(results, use_plotly=True)
            html_parts.append(f"""
    <div class="chart-container">
        <h3>Utility Score Ranking</h3>
        {fig.to_html(full_html=False, include_plotlyjs=False)}
    </div>
""")
        except Exception:
            pass

        try:
            # Radar chart
            fig = create_scenario_comparison_radar(results, use_plotly=True)
            html_parts.append(f"""
    <div class="chart-container">
        <h3>Scenario Comparison</h3>
        {fig.to_html(full_html=False, include_plotlyjs=False)}
    </div>
""")
        except Exception:
            pass

    # Weight profile
    html_parts.append(f"""
    <h2>Weight Profile: {results.weight_profile.name}</h2>
    <table>
        <tr>
            <th>Objective</th>
            <th>Weight</th>
        </tr>
""")

    for obj, weight in results.weight_profile.weights.items():
        html_parts.append(f"""
        <tr>
            <td>{obj.capitalize()}</td>
            <td>{weight:.0%}</td>
        </tr>
""")

    html_parts.append("    </table>")

    # Footer
    html_parts.append("""
    <hr>
    <p style="text-align: center; color: #7f8c8d; font-size: 12px;">
        Generated by Hallar Decision Support System
    </p>
</div>
</body>
</html>
""")

    # Write file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
