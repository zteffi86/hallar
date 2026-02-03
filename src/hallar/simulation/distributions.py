"""Probability distributions for Hallar DSS simulation."""

import numpy as np
from typing import Union

from hallar.models.scenario import PERTParams


def pert_distribution(
    a: float,
    m: float,
    b: float,
    samples: int = 10000,
    rng: np.random.Generator = None,
) -> np.ndarray:
    """
    Generate samples from PERT distribution.

    PERT is a Beta distribution scaled to [a, b] with mode at m.
    More realistic than triangular for cost/time estimates.

    Args:
        a: Minimum value
        m: Most likely value (mode)
        b: Maximum value
        samples: Number of samples to generate
        rng: Random number generator (for reproducibility)

    Returns:
        numpy array of samples from PERT distribution
    """
    if rng is None:
        rng = np.random.default_rng()

    # Handle edge case where min == max
    if a == b:
        return np.full(samples, a)

    # Handle edge case where likely is at boundaries
    if m == a:
        m = a + 0.001 * (b - a)
    elif m == b:
        m = b - 0.001 * (b - a)

    # PERT shape parameters (using lambda=4 as standard)
    alpha = 1 + 4 * (m - a) / (b - a)
    beta = 1 + 4 * (b - m) / (b - a)

    # Generate beta samples and scale to [a, b]
    beta_samples = rng.beta(alpha, beta, samples)
    return a + beta_samples * (b - a)


def pert_sample(
    params: Union[PERTParams, dict],
    rng: np.random.Generator = None,
) -> float:
    """
    Generate a single sample from PERT distribution.

    Args:
        params: PERTParams object or dict with min, likely, max keys
        rng: Random number generator (for reproducibility)

    Returns:
        Single sample value
    """
    if isinstance(params, dict):
        a, m, b = params["min"], params["likely"], params["max"]
    else:
        a, m, b = params.min, params.likely, params.max

    return pert_distribution(a, m, b, samples=1, rng=rng)[0]


def triangular_sample(
    a: float,
    m: float,
    b: float,
    rng: np.random.Generator = None,
) -> float:
    """
    Generate a single sample from triangular distribution.

    Args:
        a: Minimum value
        m: Most likely value (mode)
        b: Maximum value
        rng: Random number generator (for reproducibility)

    Returns:
        Single sample value
    """
    if rng is None:
        rng = np.random.default_rng()

    return rng.triangular(a, m, b)


def pert_mean(a: float, m: float, b: float) -> float:
    """
    Calculate the mean of a PERT distribution.

    Args:
        a: Minimum value
        m: Most likely value (mode)
        b: Maximum value

    Returns:
        Expected value (mean) of the distribution
    """
    return (a + 4 * m + b) / 6


def pert_variance(a: float, m: float, b: float) -> float:
    """
    Calculate the variance of a PERT distribution.

    Args:
        a: Minimum value
        m: Most likely value (mode)
        b: Maximum value

    Returns:
        Variance of the distribution
    """
    return ((b - a) ** 2) / 36


def pert_std(a: float, m: float, b: float) -> float:
    """
    Calculate the standard deviation of a PERT distribution.

    Args:
        a: Minimum value
        m: Most likely value (mode)
        b: Maximum value

    Returns:
        Standard deviation of the distribution
    """
    return np.sqrt(pert_variance(a, m, b))
