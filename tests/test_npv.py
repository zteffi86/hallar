"""Tests for NPV calculations."""

import pytest
import numpy as np
from hallar.simulation.npv import (
    calculate_npv,
    calculate_xnpv,
    calculate_risk_adjusted_npv,
    calculate_irr,
)


class TestNPV:
    """Tests for NPV calculation functions."""

    def test_npv_zero_discount_rate(self):
        """With 0% discount, NPV = sum of cash flows."""
        cash_flows = [-100, 50, 50, 50]
        periods = [0, 1, 2, 3]
        npv = calculate_npv(cash_flows, 0.0, periods)
        assert npv == 50

    def test_npv_positive_discount(self):
        """Higher discount rate reduces NPV."""
        cash_flows = [-100, 150]
        periods = [0, 1]

        npv_low = calculate_npv(cash_flows, 0.05, periods)
        npv_high = calculate_npv(cash_flows, 0.10, periods)

        assert npv_low > npv_high

    def test_npv_single_period(self):
        """NPV with single future cash flow."""
        cash_flows = [100]
        periods = [1]
        npv = calculate_npv(cash_flows, 0.10, periods)
        expected = 100 / 1.10
        assert abs(npv - expected) < 0.01

    def test_npv_multiple_periods(self):
        """NPV with multiple cash flows."""
        cash_flows = [-1000, 300, 400, 500]
        periods = [0, 1, 2, 3]
        rate = 0.08

        # Manual calculation
        expected = -1000 + 300 / 1.08 + 400 / (1.08 ** 2) + 500 / (1.08 ** 3)
        npv = calculate_npv(cash_flows, rate, periods)

        assert abs(npv - expected) < 0.01

    def test_npv_negative_rate_raises(self):
        """Negative discount rate should raise error."""
        with pytest.raises(ValueError):
            calculate_npv([100], -0.05, [1])

    def test_npv_negative_period_raises(self):
        """Negative period should raise error."""
        with pytest.raises(ValueError):
            calculate_npv([100], 0.05, [-1])


class TestXNPV:
    """Tests for XNPV (irregular timing)."""

    def test_xnpv_annual_matches_npv(self):
        """XNPV with annual dates should match NPV."""
        cash_flows = [-100, 50, 60]
        dates = [0, 1, 2]
        rate = 0.10

        xnpv = calculate_xnpv(cash_flows, dates, rate)
        npv = calculate_npv(cash_flows, rate, dates)

        assert abs(xnpv - npv) < 0.01

    def test_xnpv_midyear(self):
        """XNPV with mid-year cash flow."""
        cash_flows = [-100, 110]
        dates = [0, 0.5]  # 6 months
        rate = 0.10

        # After 6 months at 10% annual: 110 / (1.10^0.5)
        expected = -100 + 110 / (1.10 ** 0.5)
        xnpv = calculate_xnpv(cash_flows, dates, rate)

        assert abs(xnpv - expected) < 0.01


class TestRiskAdjustedNPV:
    """Tests for risk-adjusted NPV metrics."""

    def test_risk_metrics_positive_distribution(self):
        """Test metrics for positive NPV distribution."""
        np.random.seed(42)
        npv_dist = np.random.normal(1000, 200, 10000)

        metrics = calculate_risk_adjusted_npv(npv_dist)

        assert abs(metrics["expected_npv"] - 1000) < 20
        assert abs(metrics["std_dev"] - 200) < 20
        assert metrics["prob_loss"] < 0.01  # Very low probability of loss
        assert metrics["percentile_50"] < metrics["expected_npv"] + 50

    def test_risk_metrics_with_losses(self):
        """Test metrics for distribution with potential losses."""
        np.random.seed(42)
        npv_dist = np.random.normal(100, 300, 10000)

        metrics = calculate_risk_adjusted_npv(npv_dist)

        assert 0 < metrics["prob_loss"] < 1
        assert metrics["cvar_05"] < metrics["percentile_10"]
        assert metrics["min"] < metrics["percentile_5"]

    def test_cvar_calculation(self):
        """CVaR should be mean of worst cases."""
        # Simple distribution where we know the answer
        npv_dist = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])

        metrics = calculate_risk_adjusted_npv(npv_dist)

        # CVaR at 10% should be close to worst case (10)
        assert metrics["cvar_05"] <= 15  # Worst 5% = value 10

    def test_certainty_equivalent(self):
        """Certainty equivalent should be less than expected NPV for risk-averse."""
        np.random.seed(42)
        npv_dist = np.random.normal(1000, 500, 10000)

        metrics = calculate_risk_adjusted_npv(npv_dist, lambda_risk_aversion=2.0)

        # With positive expected NPV and variance, CE < E[NPV]
        assert metrics["certainty_equivalent"] < metrics["expected_npv"]


class TestIRR:
    """Tests for IRR calculation."""

    def test_irr_simple_case(self):
        """Test IRR for simple investment."""
        cash_flows = [-100, 110]
        periods = [0, 1]

        irr, converged = calculate_irr(cash_flows, periods)

        assert converged
        assert abs(irr - 0.10) < 0.001

    def test_irr_multiple_periods(self):
        """Test IRR with multiple cash flows."""
        cash_flows = [-1000, 400, 400, 400]
        periods = [0, 1, 2, 3]

        irr, converged = calculate_irr(cash_flows, periods)

        assert converged
        # Verify: NPV at IRR should be ~0
        npv = calculate_npv(cash_flows, irr, periods)
        assert abs(npv) < 1
