# Hallar DSS Example Data Files

This directory contains example data files for the Hallar Decision Support System.

## Files

- `scenarios_example.yaml` - Example land development scenario definitions (S0-S7)
- `market_scenarios.yaml` - Economic market condition scenarios (M1-M4)
- `weights.yaml` - Political/strategic weight profiles (P1-P6)
- `constraints.yaml` - Hard constraint definitions

## Usage

Copy these files to your working directory and modify as needed:

```bash
cp data/examples/*.yaml my_project/
```

Then run the analysis:

```bash
hallar run --scenarios my_project/scenarios_example.yaml \
           --markets my_project/market_scenarios.yaml \
           --constraints my_project/constraints.yaml \
           --weights P1 \
           --output results/
```

## Customization

### Adding New Scenarios

Add new entries under the `scenarios:` key in `scenarios_example.yaml`:

```yaml
scenarios:
  S8:
    name: "My New Scenario"
    description: "Description of the scenario"
    # ... rest of parameters
```

### Modifying Constraints

Constraints can be:
- `probabilistic` - P(metric >= threshold) must be >= confidence
- `cvar` - CVaR at alpha percentile must be >= threshold
- `deadline` - P(metric <= threshold) must be >= confidence
- `minimum` - Deterministic minimum value
- `maximum` - Deterministic maximum value
- `categorical` - Value must be in allowed set

### Custom Weight Profiles

Add new profiles under `weight_scenarios:` in `weights.yaml`. Weights are automatically normalized to sum to 1.0.
