"""Part C: estimate a rare probability honestly. TODO 4, 6 and 7."""
from __future__ import annotations

import math

import numpy as np

from avsim import space
from .search import proposal_logpdf


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """TODO 4. Wilson score interval for k successes in n trials. Must behave at k = 0 (lower bound 0,
    upper bound > 0) where the plain normal interval collapses to [0, 0]. Return (0, 1) for n = 0."""
    if n <= 0:
        return 0.0, 1.0
    if k == 0:
        z2 = z * z
        upper = z2 / (n + z2)
        return 0.0, upper
    p = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    half = z * math.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def log_weights(Z, Bn, nat: space.Natural, prop: dict, beta: float = 0.2) -> np.ndarray:
    """TODO 6. log p(u) - log q(u) for each row, where q is the DEFENSIVE MIXTURE
    q = (1 - beta) * proposal + beta * natural.

    nat.logpdf(Z, Bn) gives log p; proposal_logpdf(prop, Z, Bn) gives log of the CEM proposal.
    Use np.logaddexp so a weight of 1e-30 does not underflow to 0."""
    log_p = nat.logpdf(Z, Bn)
    log_proposal = proposal_logpdf(prop, Z, Bn)
    log_q = np.logaddexp(math.log1p(-beta) + log_proposal, math.log(beta) + log_p)
    return log_p - log_q


def is_estimate(logw: np.ndarray, y: np.ndarray, z: float = 1.96) -> dict:
    """TODO 7. Importance-sampling estimate of P(y = 1) under the natural distribution.

    w = exp(logw); p = mean(w * y)  (NOT normalised by sum(w): that version is biased for small n);
    se = std(w * y, ddof=1) / sqrt(n); CI = [max(0, p - z se), p + z se];
    Kish effective sample size ess = (sum w)^2 / sum(w^2).
    Return dict(p=, lo=, hi=, se=, ess=, n=)."""
    logw = np.asarray(logw, dtype=float)
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n == 0:
        return dict(p=0.0, lo=0.0, hi=1.0, se=0.0, ess=0.0, n=0)

    weights = np.exp(logw)
    weighted_outcomes = weights * y
    p = float(np.mean(weighted_outcomes))
    se = float(np.std(weighted_outcomes, ddof=1) / math.sqrt(n)) if n > 1 else 0.0
    ess_denom = float(np.sum(weights * weights))
    ess = float(np.sum(weights) ** 2 / ess_denom) if ess_denom > 0.0 else 0.0
    return dict(p=p, lo=max(0.0, p - z * se), hi=p + z * se, se=se, ess=ess, n=n)


def rule_of_three(n_eff: float) -> float:
    """Given: 95% upper bound on a probability when 0 events were seen in n_eff independent tries."""
    return 3.0 / max(n_eff, 1.0)
