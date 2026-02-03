"""Net Present Value calculations for Hallar DSS."""

import numpy as np
from typing import List, Dict, Any, Tuple


def calculate_npv(
    cash_flows: List[float],
    discount_rate: float,
    periods: List[int],
) -> float:
    """
    Calculate Net Present Value.

    NPV = Σ (CF_t / (1 + r)^t)

    For the city:
    - Outflows (negative): Infrastructure costs, step-in costs, management costs
    - Inflows (positive): Rights sales/lease revenue, JV dividends, profit share

    Args:
        cash_flows: Cash flows by period (negative = outflow)
        discount_rate: Per-period discount rate
        periods: Period indices for each cash flow

    Returns:
        Net Present Value
    """
    if discount_rate < 0:
        raise ValueError("Discount rate must be non-negative")

    npv = 0.0
    for cf, t in zip(cash_flows, periods):
        if t < 0:
            raise ValueError("Period must be non-negative")
        npv += cf / ((1 + discount_rate) ** t)

    return npv


def calculate_xnpv(
    cash_flows: List[float],
    dates: List[float],
    annual_rate: float,
) -> float:
    """
    Calculate NPV with irregular cash flow timing (similar to Excel XNPV).

    Args:
        cash_flows: Cash flows
        dates: Dates as year fractions (e.g., 0, 0.5, 1.25, 2.0)
        annual_rate: Annual discount rate

    Returns:
        Net Present Value
    """
    if len(cash_flows) != len(dates):
        raise ValueError("cash_flows and dates must have same length")

    npv = 0.0
    for cf, date in zip(cash_flows, dates):
        npv += cf / ((1 + annual_rate) ** date)

    return npv


def calculate_risk_adjusted_npv(
    npv_distribution: np.ndarray,
    lambda_risk_aversion: float = 2.0,
) -> Dict[str, float]:
    """
    Calculate multiple risk-adjusted NPV metrics.

    Metrics:
    1. Expected NPV: E[NPV]
    2. Certainty Equivalent: CE = E[NPV] - λ * Var[NPV] / (2 * E[NPV])
    3. CVaR (Conditional Value at Risk): Expected loss in worst α% of cases
    4. Probability of Loss: P(NPV < 0)

    Args:
        npv_distribution: Array of NPV samples from Monte Carlo simulation
        lambda_risk_aversion: Risk aversion parameter for certainty equivalent

    Returns:
        Dictionary with risk metrics
    """
    expected_npv = float(np.mean(npv_distribution))
    variance = float(np.var(npv_distribution))
    std_dev = float(np.std(npv_distribution))

    # Certainty equivalent (mean-variance utility)
    if expected_npv > 0 and abs(expected_npv) > 1e-10:
        certainty_equivalent = expected_npv - (lambda_risk_aversion * variance) / (2 * expected_npv)
    else:
        certainty_equivalent = expected_npv - lambda_risk_aversion * std_dev

    # CVaR at 5% (expected value in worst 5% of outcomes)
    percentile_5 = np.percentile(npv_distribution, 5)
    worst_5_pct = npv_distribution[npv_distribution <= percentile_5]
    cvar_05 = float(np.mean(worst_5_pct)) if len(worst_5_pct) > 0 else float(percentile_5)

    # CVaR at 10%
    percentile_10 = np.percentile(npv_distribution, 10)
    worst_10_pct = npv_distribution[npv_distribution <= percentile_10]
    cvar_10 = float(np.mean(worst_10_pct)) if len(worst_10_pct) > 0 else float(percentile_10)

    # Probability of loss
    prob_loss = float(np.mean(npv_distribution < 0))

    return {
        "expected_npv": expected_npv,
        "std_dev": std_dev,
        "variance": variance,
        "certainty_equivalent": certainty_equivalent,
        "cvar_05": cvar_05,
        "cvar_10": cvar_10,
        "prob_loss": prob_loss,
        "percentile_5": float(np.percentile(npv_distribution, 5)),
        "percentile_10": float(np.percentile(npv_distribution, 10)),
        "percentile_25": float(np.percentile(npv_distribution, 25)),
        "percentile_50": float(np.percentile(npv_distribution, 50)),
        "percentile_75": float(np.percentile(npv_distribution, 75)),
        "percentile_90": float(np.percentile(npv_distribution, 90)),
        "percentile_95": float(np.percentile(npv_distribution, 95)),
        "min": float(np.min(npv_distribution)),
        "max": float(np.max(npv_distribution)),
    }


def calculate_irr(
    cash_flows: List[float],
    periods: List[int],
    initial_guess: float = 0.1,
    max_iterations: int = 100,
    tolerance: float = 1e-6,
) -> Tuple[float, bool]:
    """
    Calculate Internal Rate of Return using Newton-Raphson method.

    IRR is the discount rate that makes NPV = 0.

    Args:
        cash_flows: Cash flows by period
        periods: Period indices
        initial_guess: Starting guess for IRR
        max_iterations: Maximum iterations for convergence
        tolerance: Convergence tolerance

    Returns:
        Tuple of (IRR, converged)
    """
    rate = initial_guess

    for _ in range(max_iterations):
        # Calculate NPV and its derivative
        npv = 0.0
        dnpv = 0.0
        for cf, t in zip(cash_flows, periods):
            if t > 0:
                npv += cf / ((1 + rate) ** t)
                dnpv -= t * cf / ((1 + rate) ** (t + 1))
            else:
                npv += cf

        if abs(dnpv) < 1e-12:
            # Derivative too small, cannot continue
            return rate, False

        # Newton-Raphson update
        new_rate = rate - npv / dnpv

        if abs(new_rate - rate) < tolerance:
            return new_rate, True

        rate = new_rate

    return rate, False
