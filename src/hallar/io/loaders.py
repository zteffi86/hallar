"""YAML/JSON data loaders for Hallar DSS."""

import yaml
from pathlib import Path
from typing import Dict, List, Union, Any, BinaryIO

from hallar.models.scenario import Scenario
from hallar.models.market import MarketScenario
from hallar.models.constraints import ConstraintSet
from hallar.models.weights import WeightProfile


def _load_yaml(source: Union[str, Path, BinaryIO]) -> Dict[str, Any]:
    """Load YAML from file path or file-like object."""
    if isinstance(source, (str, Path)):
        with open(source, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        return yaml.safe_load(source)


def load_scenarios(source: Union[str, Path, BinaryIO]) -> List[Scenario]:
    """
    Load scenario definitions from YAML file.

    Args:
        source: File path or file-like object containing scenarios YAML

    Returns:
        List of Scenario objects
    """
    data = _load_yaml(source)

    scenarios = []
    for id, scenario_data in data.get("scenarios", {}).items():
        scenarios.append(Scenario.from_dict(id, scenario_data))

    return sorted(scenarios, key=lambda s: s.id)


def load_markets(source: Union[str, Path, BinaryIO]) -> List[MarketScenario]:
    """
    Load market scenario definitions from YAML file.

    Args:
        source: File path or file-like object containing market scenarios YAML

    Returns:
        List of MarketScenario objects
    """
    data = _load_yaml(source)

    markets = []
    for id, market_data in data.get("market_scenarios", {}).items():
        markets.append(MarketScenario.from_dict(id, market_data))

    return sorted(markets, key=lambda m: m.id)


def load_constraints(source: Union[str, Path, BinaryIO]) -> ConstraintSet:
    """
    Load constraint definitions from YAML file.

    Args:
        source: File path or file-like object containing constraints YAML

    Returns:
        ConstraintSet object
    """
    data = _load_yaml(source)
    return ConstraintSet.from_dict(data.get("constraints", {}))


def load_weights(source: Union[str, Path, BinaryIO]) -> List[WeightProfile]:
    """
    Load weight profile definitions from YAML file.

    Args:
        source: File path or file-like object containing weights YAML

    Returns:
        List of WeightProfile objects
    """
    data = _load_yaml(source)

    profiles = []
    for id, profile_data in data.get("weight_scenarios", {}).items():
        profiles.append(WeightProfile.from_dict(id, profile_data))

    return sorted(profiles, key=lambda p: p.id)


def load_all(
    scenarios_path: Union[str, Path],
    markets_path: Union[str, Path],
    constraints_path: Union[str, Path],
    weights_path: Union[str, Path],
) -> Dict[str, Any]:
    """
    Load all data files at once.

    Returns:
        Dict with 'scenarios', 'markets', 'constraints', 'weights' keys
    """
    return {
        "scenarios": load_scenarios(scenarios_path),
        "markets": load_markets(markets_path),
        "constraints": load_constraints(constraints_path),
        "weights": load_weights(weights_path),
    }
