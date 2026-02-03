"""Tests for probability distributions."""

import pytest
import numpy as np
from hallar.simulation.distributions import (
    pert_distribution,
    pert_sample,
    pert_mean,
    pert_variance,
    triangular_sample,
)
from hallar.models.scenario import PERTParams


class TestPERTDistribution:
    """Tests for PERT distribution functions."""

    def test_pert_distribution_bounds(self):
        """PERT samples should be within [min, max]."""
        samples = pert_distribution(10, 15, 20, samples=10000)
        assert samples.min() >= 10
        assert samples.max() <= 20

    def test_pert_distribution_mode_right_skewed(self):
        """PERT with mode near max should be right-skewed."""
        samples = pert_distribution(10, 18, 20, samples=100000)
        # Median should be between mode and mean
        assert np.median(samples) > 15
        assert np.median(samples) < 19

    def test_pert_distribution_mode_left_skewed(self):
        """PERT with mode near min should be left-skewed."""
        samples = pert_distribution(10, 12, 20, samples=100000)
        assert np.median(samples) < 15

    def test_pert_distribution_symmetric(self):
        """PERT with mode at center should be roughly symmetric."""
        samples = pert_distribution(10, 15, 20, samples=100000)
        mean = np.mean(samples)
        # Mean should be close to mode for symmetric case
        assert abs(mean - 15) < 0.5

    def test_pert_distribution_reproducibility(self):
        """Same seed should produce same results."""
        rng1 = np.random.default_rng(42)
        rng2 = np.random.default_rng(42)

        samples1 = pert_distribution(10, 15, 20, samples=100, rng=rng1)
        samples2 = pert_distribution(10, 15, 20, samples=100, rng=rng2)

        np.testing.assert_array_equal(samples1, samples2)

    def test_pert_distribution_edge_case_equal_bounds(self):
        """PERT with min == max should return constant."""
        samples = pert_distribution(15, 15, 15, samples=100)
        np.testing.assert_array_equal(samples, np.full(100, 15))

    def test_pert_sample_from_params(self):
        """pert_sample should work with PERTParams object."""
        params = PERTParams(min=10, likely=15, max=20)
        sample = pert_sample(params)
        assert 10 <= sample <= 20

    def test_pert_sample_from_dict(self):
        """pert_sample should work with dict."""
        params = {"min": 10, "likely": 15, "max": 20}
        sample = pert_sample(params)
        assert 10 <= sample <= 20

    def test_pert_mean_formula(self):
        """Test PERT mean calculation (a + 4m + b) / 6."""
        mean = pert_mean(10, 15, 20)
        expected = (10 + 4 * 15 + 20) / 6
        assert abs(mean - expected) < 0.001

    def test_pert_variance_formula(self):
        """Test PERT variance calculation."""
        variance = pert_variance(10, 15, 20)
        expected = ((20 - 10) ** 2) / 36
        assert abs(variance - expected) < 0.001


class TestTriangularDistribution:
    """Tests for triangular distribution."""

    def test_triangular_bounds(self):
        """Triangular samples should be within [a, b]."""
        rng = np.random.default_rng(42)
        samples = [triangular_sample(10, 15, 20, rng=rng) for _ in range(1000)]
        assert min(samples) >= 10
        assert max(samples) <= 20
