# Hallar Decision Support System

A quantitative decision support system for comparing land development scenarios using Monte Carlo simulation.

## Overview

Hallar DSS helps municipalities and planners evaluate different land development contract structures by:

1. **Loading scenario definitions** - Different contract structures (S0-S20)
2. **Simulating market conditions** - Various economic scenarios (M1-M4)
3. **Applying political weights** - Priority profiles (P1-P4) for objectives
4. **Running Monte Carlo simulation** - 10,000+ iterations per scenario
5. **Checking constraints** - Hard requirements (financial, timing, affordability)
6. **Ranking scenarios** - By weighted utility score
7. **Generating reports** - Excel, PDF, HTML, and interactive dashboards

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/hallar-dss.git
cd hallar-dss

# Install with pip
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

### 1. Initialize a new project with example data

```bash
hallar init --output ./my_project
```

This creates example YAML files you can customize.

### 2. Run analysis

```bash
hallar run \
  --scenarios my_project/scenarios_example.yaml \
  --markets my_project/market_scenarios.yaml \
  --constraints my_project/constraints.yaml \
  --weights P1 \
  --simulations 10000 \
  --output results/
```

### 3. Launch web interface

```bash
hallar ui
```

Then open http://localhost:8501 in your browser.

## Data Files

### Scenarios (scenarios.yaml)

Define land development contract structures:

```yaml
scenarios:
  S0:
    name: "Baseline - City sells rights"
    description: "Traditional procurement approach"

    infrastructure_cost:
      min: 8000      # ISK millions
      likely: 12000
      max: 20000

    rights_revenue:
      min: 15000
      likely: 18000
      max: 22000

    timeline:
      first_units:
        min: 36       # months
        likely: 48
        max: 72
      first_school:
        min: 48
        likely: 60
        max: 84

    risks:
      cost_overrun_probability: 0.6
      cost_overrun_multiplier:
        min: 1.0
        likely: 1.15
        max: 1.5
      developer_default_probability: 0.05
      delay_probability: 0.4
      delay_months:
        min: 0
        likely: 6
        max: 24

    affordability:
      percentage_affordable: 0.25
      price_discount: 0.15
      restriction_years: 30
      legally_binding: true

    quality:
      energy_rating: "A"
      defect_rate:
        min: 0.01
        likely: 0.03
        max: 0.07

    city_control: 0.7
    step_in_cost_fraction: 0.25
```

### Market Scenarios (market_scenarios.yaml)

Define economic conditions:

```yaml
market_scenarios:
  M1:
    name: "Optimistic"
    probability: 0.20
    parameters:
      construction_cost_multiplier: 1.05
      interest_rate: 0.05
      property_price_growth: 0.03
      sales_velocity_months: 12
      inflation_rate: 0.025

  M2:
    name: "Base Case"
    probability: 0.50
    parameters:
      construction_cost_multiplier: 1.15
      interest_rate: 0.07
      property_price_growth: 0.01
      sales_velocity_months: 18
      inflation_rate: 0.04
```

### Constraints (constraints.yaml)

Define hard requirements:

```yaml
constraints:
  financial:
    name: "City must not lose money"
    type: "probabilistic"
    metric: "npv"
    threshold: 0
    confidence: 0.90    # P(NPV >= 0) must be >= 90%

  school_timing:
    name: "School must be operational"
    type: "deadline"
    metric: "first_school_months"
    threshold: 60
    confidence: 0.80

  affordability_minimum:
    name: "Minimum affordable housing"
    type: "minimum"
    metric: "affordable_percentage"
    threshold: 0.25
```

### Weight Profiles (weights.yaml)

Define objective priorities:

```yaml
weight_scenarios:
  P1:
    name: "Balanced"
    weights:
      speed: 0.30
      affordability: 0.30
      quality: 0.30
      financial: 0.10

  P2:
    name: "Housing Crisis"
    weights:
      speed: 0.25
      affordability: 0.40
      quality: 0.20
      financial: 0.15
```

## Output

### Text Summary

```
═══════════════════════════════════════════════════════════════════════
                    HALLAR DECISION SUPPORT SYSTEM
                         Results Summary
═══════════════════════════════════════════════════════════════════════
 Simulation: 10,000 iterations | Weight Profile: Balanced
 Date: 2026-02-03 | Scenarios: 8 | Passed: 5
═══════════════════════════════════════════════════════════════════════

 TOP 3 SCENARIOS (by utility score)
───────────────────────────────────────────────────────────────────────
 #1: S1 - Milestone-vesting PPP
     Utility: 0.723 | E[NPV]: 2,340M | P(loss): 8.2% | Time: 42 months
     Status: All constraints passed

 #2: S7 - Joint Venture
     Utility: 0.681 | E[NPV]: 1,890M | P(loss): 11.5% | Time: 48 months
     Status: All constraints passed
```

### Export Formats

- **Excel** - Multi-sheet workbook with results, charts, and sensitivity analysis
- **PDF** - Formatted report with executive summary
- **JSON** - Machine-readable results for integration
- **HTML** - Interactive report with embedded charts

## Python API

```python
from hallar import (
    load_scenarios, load_markets, load_constraints,
    run_full_analysis, WeightProfile
)

# Load data
scenarios = load_scenarios("scenarios.yaml")
markets = load_markets("markets.yaml")
constraints = load_constraints("constraints.yaml")

# Create weight profile
weights = WeightProfile.create_custom(
    speed=0.25,
    affordability=0.30,
    quality=0.25,
    financial=0.20
)

# Run analysis
results = run_full_analysis(
    scenarios=scenarios,
    markets=markets,
    constraints=constraints,
    weights=weights,
    n_simulations=10000,
    random_seed=42
)

# Access results
for result in results.ranked_results[:3]:
    print(f"{result.scenario.id}: Utility={result.utility:.3f}")
```

## Key Concepts

### PERT Distribution

Uncertain parameters use PERT (Program Evaluation and Review Technique) distributions:
- More realistic than uniform or triangular
- Defined by min, most likely, and max values
- Mode is weighted more heavily than extremes

### NPV Calculation

Net Present Value accounts for:
- Time value of money (discount rate from market scenario)
- Phased cash flows (costs during construction, revenue at completion)
- Risk events (cost overruns, delays, developer defaults)

### Utility Scoring

Multi-objective utility function:
```
U(s) = w_speed × u(time) + w_afford × u(affordability) +
       w_quality × u(quality) + w_financial × u(npv)
```

Where each sub-utility is normalized to [0, 1].

### Constraint Types

| Type | Description | Example |
|------|-------------|---------|
| `probabilistic` | P(metric ≥ threshold) ≥ confidence | P(NPV ≥ 0) ≥ 90% |
| `cvar` | CVaR at α ≥ threshold | Expected loss in worst 5% ≥ -2B |
| `deadline` | P(metric ≤ threshold) ≥ confidence | P(school ≤ 60mo) ≥ 80% |
| `minimum` | metric ≥ threshold | affordable% ≥ 25% |
| `categorical` | metric ∈ allowed | energy_rating ∈ [A+, A] |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=hallar --cov-report=html

# Format code
black src/
ruff check src/
```

## Project Structure

```
hallar-dss/
├── pyproject.toml
├── README.md
├── data/
│   └── examples/
│       ├── scenarios_example.yaml
│       ├── market_scenarios.yaml
│       ├── weights.yaml
│       └── constraints.yaml
├── src/
│   └── hallar/
│       ├── models/          # Data classes
│       ├── simulation/      # Monte Carlo engine
│       ├── analysis/        # Ranking, sensitivity
│       ├── visualization/   # Charts, reports
│       ├── io/              # Loaders, exporters
│       └── cli.py           # Command line interface
├── app/
│   └── streamlit_app.py     # Web interface
└── tests/
    └── test_*.py
```

## License

MIT License
