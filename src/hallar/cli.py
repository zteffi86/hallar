"""Command-line interface for Hallar DSS."""

import sys
from pathlib import Path
from typing import Optional

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="hallar")
def main():
    """Hallar Decision Support System - Land Development Scenario Analysis."""
    pass


@main.command()
@click.option(
    "--scenarios", "-s",
    type=click.Path(exists=True),
    required=True,
    help="Path to scenarios YAML file",
)
@click.option(
    "--markets", "-m",
    type=click.Path(exists=True),
    required=True,
    help="Path to market scenarios YAML file",
)
@click.option(
    "--constraints", "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to constraints YAML file",
)
@click.option(
    "--weights", "-w",
    type=str,
    default="P1",
    help="Weight profile ID (e.g., P1, P2) or path to weights YAML file",
)
@click.option(
    "--simulations", "-n",
    type=int,
    default=10000,
    help="Number of Monte Carlo simulations",
)
@click.option(
    "--seed",
    type=int,
    default=42,
    help="Random seed for reproducibility",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./results",
    help="Output directory for results",
)
@click.option(
    "--format", "-f",
    type=click.Choice(["text", "json", "excel", "html", "all"]),
    default="text",
    help="Output format",
)
def run(
    scenarios: str,
    markets: str,
    constraints: str,
    weights: str,
    simulations: int,
    seed: int,
    output: str,
    format: str,
):
    """Run Monte Carlo analysis on land development scenarios."""
    from hallar.io.loaders import load_scenarios, load_markets, load_constraints, load_weights
    from hallar.simulation.monte_carlo import run_full_analysis
    from hallar.visualization.reports import generate_text_summary, generate_summary_report
    from hallar.io.exporters import export_to_json, export_to_excel

    click.echo("Loading data files...")

    # Load scenarios
    scenario_list = load_scenarios(scenarios)
    click.echo(f"  Loaded {len(scenario_list)} scenarios")

    # Load markets
    market_list = load_markets(markets)
    click.echo(f"  Loaded {len(market_list)} market scenarios")

    # Load constraints
    constraint_set = load_constraints(constraints)
    click.echo(f"  Loaded {len(constraint_set.constraints)} constraints")

    # Load or select weight profile
    if Path(weights).exists():
        weight_profiles = load_weights(weights)
        weight_profile = weight_profiles[0]  # Use first profile
    else:
        # Look for profile by ID in default weights file
        try:
            weights_file = Path(scenarios).parent / "weights.yaml"
            if weights_file.exists():
                weight_profiles = load_weights(weights_file)
            else:
                # Use a default file from examples
                default_weights = Path(__file__).parent.parent.parent / "data" / "examples" / "weights.yaml"
                if default_weights.exists():
                    weight_profiles = load_weights(default_weights)
                else:
                    # Create default profile
                    from hallar.models.weights import WeightProfile
                    weight_profile = WeightProfile.create_custom(0.25, 0.25, 0.25, 0.25)
                    weight_profiles = [weight_profile]

            weight_profile = next((p for p in weight_profiles if p.id == weights), None)
            if weight_profile is None:
                click.echo(f"Warning: Weight profile '{weights}' not found, using first available")
                weight_profile = weight_profiles[0]
        except Exception:
            from hallar.models.weights import WeightProfile
            weight_profile = WeightProfile.create_custom(0.25, 0.25, 0.25, 0.25)

    click.echo(f"  Using weight profile: {weight_profile.name}")

    # Create output directory
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run simulation
    click.echo(f"\nRunning {simulations:,} Monte Carlo simulations...")

    with click.progressbar(length=100, label="Simulating") as bar:
        results = run_full_analysis(
            scenarios=scenario_list,
            markets=market_list,
            constraints=constraint_set,
            weights=weight_profile,
            n_simulations=simulations,
            random_seed=seed,
        )
        bar.update(100)

    click.echo("\nAnalysis complete!")
    click.echo(f"  Scenarios evaluated: {len(results.scenario_results)}")
    click.echo(f"  Passed constraints: {len(results.passed_scenarios)}")
    click.echo(f"  Failed constraints: {len(results.failed_scenarios)}")

    # Generate outputs
    if format in ["text", "all"]:
        summary = generate_text_summary(results)
        click.echo("\n" + summary)

        summary_path = output_dir / "summary.txt"
        with open(summary_path, "w") as f:
            f.write(summary)
        click.echo(f"\nText summary saved to: {summary_path}")

    if format in ["json", "all"]:
        json_path = output_dir / "results.json"
        export_to_json(results, json_path)
        click.echo(f"JSON results saved to: {json_path}")

    if format in ["excel", "all"]:
        excel_path = output_dir / "results.xlsx"
        export_to_excel(results, excel_path)
        click.echo(f"Excel report saved to: {excel_path}")

    if format in ["html", "all"]:
        html_path = output_dir / "report.html"
        generate_summary_report(results, html_path)
        click.echo(f"HTML report saved to: {html_path}")


@main.command()
@click.option(
    "--port", "-p",
    type=int,
    default=8501,
    help="Port to run the web interface on",
)
@click.option(
    "--data-dir", "-d",
    type=click.Path(exists=True),
    help="Directory containing data files",
)
def ui(port: int, data_dir: Optional[str]):
    """Launch the Streamlit web interface."""
    import subprocess

    app_path = Path(__file__).parent.parent.parent / "app" / "streamlit_app.py"

    if not app_path.exists():
        click.echo(f"Error: Streamlit app not found at {app_path}")
        sys.exit(1)

    cmd = ["streamlit", "run", str(app_path), "--server.port", str(port)]

    if data_dir:
        cmd.extend(["--", "--data-dir", data_dir])

    click.echo(f"Starting Hallar DSS web interface on port {port}...")
    click.echo("Press Ctrl+C to stop")

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        click.echo("\nShutting down...")


@main.command()
@click.argument("results_file", type=click.Path(exists=True))
@click.option(
    "--format", "-f",
    type=click.Choice(["excel", "pdf", "json"]),
    required=True,
    help="Export format",
)
@click.option(
    "--output", "-o",
    type=click.Path(),
    required=True,
    help="Output file path",
)
def export(results_file: str, format: str, output: str):
    """Export results to different formats."""
    import json
    from hallar.io.exporters import export_to_excel, export_to_json, export_to_pdf

    click.echo(f"Loading results from {results_file}...")

    # Load JSON results
    with open(results_file, "r") as f:
        data = json.load(f)

    # For now, we need to reconstruct the results object
    # This is a simplified export that works with JSON data directly
    click.echo(f"Exporting to {format}...")

    if format == "json":
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
    elif format == "excel":
        # Create a simple Excel export from JSON
        import pandas as pd

        if "results" in data:
            df = pd.DataFrame(data["results"])
            df.to_excel(output, index=False)
        else:
            click.echo("Error: Invalid results format")
            sys.exit(1)
    elif format == "pdf":
        click.echo("PDF export requires full results object. Use 'hallar run --format all' instead.")
        sys.exit(1)

    click.echo(f"Exported to: {output}")


@main.command()
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./data",
    help="Output directory for example files",
)
def init(output: str):
    """Initialize a new project with example data files."""
    import shutil

    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)

    examples_dir = Path(__file__).parent.parent.parent / "data" / "examples"

    if not examples_dir.exists():
        click.echo("Error: Example data directory not found")
        sys.exit(1)

    files = [
        "scenarios_example.yaml",
        "market_scenarios.yaml",
        "weights.yaml",
        "constraints.yaml",
    ]

    click.echo(f"Copying example files to {output_dir}...")

    for file in files:
        src = examples_dir / file
        dst = output_dir / file
        if src.exists():
            shutil.copy(src, dst)
            click.echo(f"  Created: {dst}")

    click.echo("\nExample files created. Edit them to match your scenarios.")
    click.echo("\nNext steps:")
    click.echo(f"  1. Edit the files in {output_dir}")
    click.echo(f"  2. Run: hallar run -s {output_dir}/scenarios_example.yaml \\")
    click.echo(f"              -m {output_dir}/market_scenarios.yaml \\")
    click.echo(f"              -c {output_dir}/constraints.yaml \\")
    click.echo(f"              -w P1")


@main.command()
@click.argument("scenario_file", type=click.Path(exists=True))
def validate(scenario_file: str):
    """Validate scenario data files."""
    from hallar.io.loaders import load_scenarios, load_markets, load_constraints, load_weights

    click.echo(f"Validating {scenario_file}...")

    try:
        # Try to determine file type and validate
        file_path = Path(scenario_file)
        file_name = file_path.name.lower()

        if "scenario" in file_name:
            data = load_scenarios(scenario_file)
            click.echo(f"  Valid scenarios file with {len(data)} scenarios")
            for s in data:
                click.echo(f"    - {s.id}: {s.name}")

        elif "market" in file_name:
            data = load_markets(scenario_file)
            click.echo(f"  Valid market scenarios file with {len(data)} markets")
            for m in data:
                click.echo(f"    - {m.id}: {m.name} (p={m.probability:.0%})")

        elif "constraint" in file_name:
            data = load_constraints(scenario_file)
            click.echo(f"  Valid constraints file with {len(data.constraints)} constraints")
            for cid, c in data.constraints.items():
                click.echo(f"    - {cid}: {c.name} ({c.type.value})")

        elif "weight" in file_name:
            data = load_weights(scenario_file)
            click.echo(f"  Valid weights file with {len(data)} profiles")
            for w in data:
                click.echo(f"    - {w.id}: {w.name}")

        else:
            # Try each loader
            try:
                data = load_scenarios(scenario_file)
                click.echo(f"  Valid scenarios file with {len(data)} scenarios")
            except Exception:
                try:
                    data = load_markets(scenario_file)
                    click.echo(f"  Valid market scenarios file with {len(data)} markets")
                except Exception:
                    try:
                        data = load_constraints(scenario_file)
                        click.echo(f"  Valid constraints file")
                    except Exception:
                        data = load_weights(scenario_file)
                        click.echo(f"  Valid weights file")

        click.echo("\nValidation passed!")

    except Exception as e:
        click.echo(f"Validation failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
