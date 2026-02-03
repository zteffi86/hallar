"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path


@pytest.fixture
def example_data_dir():
    """Path to example data directory."""
    return Path(__file__).parent.parent / "data" / "examples"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test outputs."""
    return tmp_path / "hallar_test_output"
