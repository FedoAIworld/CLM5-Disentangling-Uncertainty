"""Evaluation metrics used in the manuscript.

Implements
----------
CP      Coverage percentage using summary["lb"] and summary["ub"].
MBE     Mean bias.
RMSE    Root mean square error.
ubRMSE  Unbiased RMSE = sqrt(RMSE^2 - MBE^2).
sigma   Ensemble spread averaged over valid observation times.
SS      sigma / ubRMSE.

Important
---------
The CP envelope is controlled upstream in ``summaries.ensemble_summary``.
That function decides whether ``lb``/``ub`` are min/max or quantile bounds.
This keeps CP, plots, and merged plot-input files consistent.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _align(obs, pred) -> tuple[np.ndarray, np.ndarray]:
    """Return paired non-NaN obs/pred arrays."""
    obs = np.asarray(obs, dtype=float)
    pred = np.asarray(pred, dtype=float)

    if obs.shape != pred.shape:
        raise ValueError(f"Shape mismatch: obs {obs.shape} vs pred {pred.shape}")

    mask = ~(np.isnan(obs) | np.isnan(pred))
    return obs[mask], pred[mask]


# ---------------------------------------------------------------------------
# Individual metrics
# ---------------------------------------------------------------------------
def mbe(obs, pred) -> float:
    """Mean bias error: mean(pred - obs)."""
    o, p = _align(obs, pred)
    if o.size == 0:
        return np.nan
    return float(np.mean(p - o))


def rmse(obs, pred) -> float:
    """Root mean square error."""
    o, p = _align(obs, pred)
    if o.size == 0:
        return np.nan
    return float(np.sqrt(np.mean((p - o) ** 2)))


def ubrmse(obs, pred) -> float:
    """Unbiased RMSE = sqrt(RMSE^2 - MBE^2)."""
    o, p = _align(obs, pred)
    if o.size == 0:
        return np.nan

    r = np.sqrt(np.mean((p - o) ** 2))
    b = np.mean(p - o)

    # Guard against tiny negative values from floating-point noise.
    diff = max(r * r - b * b, 0.0)
    return float(np.sqrt(diff))


def coverage_percent(
    obs_series: pd.Series,
    lb_series: pd.Series,
    ub_series: pd.Series,
) -> float:
    """Percentage of observed points lying inside [lb, ub].

    Only non-NaN observation times contribute to the denominator.

    If lb/ub are NaN at a valid observation time, that point is counted as not
    covered because the comparison returns False.
    """
    mask = obs_series.notna()
    n = int(mask.sum())

    if n == 0:
        return np.nan

    inside = ((obs_series >= lb_series) & (obs_series <= ub_series))[mask]
    return float(100.0 * inside.sum() / n)


def ensemble_spread_sigma(member_matrix: np.ndarray) -> float:
    """Mean of the per-timestep ensemble standard deviation.

    This is independent of the CP envelope. It always uses the actual
    ensemble-member matrix and computes standard deviation across members
    at each timestep, then averages over timesteps.
    """
    if member_matrix.size == 0:
        return np.nan

    per_t = np.nanstd(member_matrix, axis=1, ddof=1)
    return float(np.nanmean(per_t))


def skill_spread_ratio(sigma: float, ubrmse_value: float) -> float:
    """Spread-skill ratio = sigma / ubRMSE."""
    if ubrmse_value is None or np.isnan(ubrmse_value) or ubrmse_value == 0:
        return np.nan
    return float(sigma / ubrmse_value)


# ---------------------------------------------------------------------------
# High-level metric calculation
# ---------------------------------------------------------------------------
def compute_all(
    summary: pd.DataFrame,
    members: pd.DataFrame,
    obs: pd.Series,
    month_filter: Iterable[int] | None = None,
) -> dict[str, float | int | str]:
    """Compute all metrics for one experiment/site/variable.

    Parameters
    ----------
    summary
        DataFrame with ``datetime``, ``mean``, ``lb`` and ``ub`` columns.
        The meaning of ``lb``/``ub`` is controlled by
        ``summaries.ensemble_summary``. They may be min/max or quantile bounds.

    members
        Wide ensemble DataFrame with ``datetime`` plus ``real_*`` columns.

    obs
        Observation series indexed by datetime.

    month_filter
        Optional iterable of months, 1-12. Used for growing-season metrics.

    Returns
    -------
    dict
        Metric values plus bookkeeping fields.
    """
    if obs is None:
        obs = pd.Series(dtype=float)

    if obs.empty:
        return {
            "CP": np.nan,
            "MBE": np.nan,
            "RMSE": np.nan,
            "ubRMSE": np.nan,
            "sigma": np.nan,
            "SS": np.nan,
            "n_obs": 0,
            "n_total": int(len(summary)),
            "envelope": (
                str(summary["envelope"].dropna().iloc[0])
                if "envelope" in summary.columns and summary["envelope"].notna().any()
                else "unknown"
            ),
        }

    required = {"datetime", "mean", "lb", "ub"}
    if not required.issubset(summary.columns):
        missing = sorted(required - set(summary.columns))
        raise KeyError(f"summary is missing required columns: {missing}")

    # Join observations by datetime.
    obs_df = obs.rename("obs").to_frame().reset_index()
    obs_df.columns = ["datetime", "obs"]

    merged = summary.merge(obs_df, on="datetime", how="left")

    if month_filter is not None:
        month_filter = list(month_filter)
        merged = merged[merged["datetime"].dt.month.isin(month_filter)]

    cp_val = coverage_percent(merged["obs"], merged["lb"], merged["ub"])

    mbe_val = mbe(merged["obs"], merged["mean"])
    rmse_val = rmse(merged["obs"], merged["mean"])
    ub_val = ubrmse(merged["obs"], merged["mean"])

    # Ensemble spread sigma must use the same valid observation times as
    # ubRMSE, but it is calculated from the ensemble-member matrix, not lb/ub.
    member_cols = [c for c in members.columns if c.startswith("real_")]

    if not member_cols:
        sigma_val = np.nan
    else:
        if month_filter is not None:
            mem_mask = members["datetime"].dt.month.isin(month_filter)
        else:
            mem_mask = np.ones(len(members), dtype=bool)

        valid_times = merged.loc[merged["obs"].notna(), "datetime"]
        mem_mask &= members["datetime"].isin(valid_times)

        sigma_val = ensemble_spread_sigma(
            members.loc[mem_mask, member_cols].to_numpy(dtype=float)
        )

    ss_val = skill_spread_ratio(sigma_val, ub_val)

    envelope = (
        str(summary["envelope"].dropna().iloc[0])
        if "envelope" in summary.columns and summary["envelope"].notna().any()
        else "unknown"
    )

    return {
        "CP": cp_val,
        "MBE": mbe_val,
        "RMSE": rmse_val,
        "ubRMSE": ub_val,
        "sigma": sigma_val,
        "SS": ss_val,
        "n_obs": int(merged["obs"].notna().sum()),
        "n_total": int(len(merged)),
        "envelope": envelope,
    }