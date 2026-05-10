"""Ensemble summary statistics.

Given a wide ensemble dataframe (``datetime`` + ``real_0 ... real_N``), this
module produces a per-timestep summary table with mean, median, std, min,
max, 25th / 75th percentiles, IQR, and configurable lower/upper ensemble
bounds.

Envelope options
----------------
The ``ensemble_summary`` function supports two envelope definitions:

    envelope="minmax"
        lb = ensemble minimum
        ub = ensemble maximum

    envelope="quantile"
        lb = lower_q quantile
        ub = upper_q quantile

The function always writes both min/max and p005/p995 columns. The active
ensemble envelope used by downstream metrics and plots is written to lb/ub.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

_REAL_COLS_PATTERN = "real_"


def _member_cols(df: pd.DataFrame) -> list[str]:
    """Return ensemble-member columns in stable real_* order."""
    cols = [c for c in df.columns if c.startswith(_REAL_COLS_PATTERN)]

    def _member_number(col: str) -> int:
        try:
            return int(col.split("_", 1)[1])
        except Exception:
            return 10**9

    return sorted(cols, key=_member_number)


def ensemble_summary(
    df: pd.DataFrame,
    envelope: str = "minmax",
    lower_q: float = 0.005,
    upper_q: float = 0.995,
) -> pd.DataFrame:
    """Compute per-timestep ensemble summary statistics.

    Parameters
    ----------
    df
        Wide ensemble dataframe with ``datetime`` and ``real_*`` columns.

    envelope
        Method used to define ``lb`` and ``ub``.

        ``"minmax"``
            ``lb`` is the ensemble minimum and ``ub`` is the ensemble maximum.

        ``"quantile"``
            ``lb`` is the ``lower_q`` quantile and ``ub`` is the ``upper_q``
            quantile.

    lower_q, upper_q
        Quantile levels used when ``envelope="quantile"``. Defaults are
        0.005 and 0.995, corresponding to the central 99% interval.

    Returns
    -------
    DataFrame
        Columns include:

        ``datetime``
        ``mean``
        ``median``
        ``std``
        ``min``
        ``max``
        ``q25``
        ``q75``
        ``iqr``
        ``p005``
        ``p995``
        ``lb``
        ``ub``
        ``envelope``
        ``lower_q``
        ``upper_q``
        ``n_members``

    Notes
    -----
    ``min`` and ``max`` are always the full ensemble envelope.

    ``p005`` and ``p995`` are always the configured lower/upper quantiles.

    ``lb`` and ``ub`` are the active envelope used by metrics and plots.
    """
    cols = _member_cols(df)
    if not cols:
        raise ValueError("No 'real_*' columns found in ensemble dataframe")

    if "datetime" not in df.columns:
        raise ValueError("Expected a 'datetime' column in ensemble dataframe")

    if envelope not in {"minmax", "quantile"}:
        raise ValueError(
            f"Unknown envelope={envelope!r}; use 'minmax' or 'quantile'"
        )

    if not (0.0 <= lower_q < upper_q <= 1.0):
        raise ValueError(
            f"Invalid quantile bounds: lower_q={lower_q}, upper_q={upper_q}"
        )

    members = df[cols].to_numpy(dtype=float)

    out = pd.DataFrame({"datetime": df["datetime"].values})

    out["mean"] = np.nanmean(members, axis=1)
    out["median"] = np.nanmedian(members, axis=1)
    out["std"] = np.nanstd(members, axis=1, ddof=1)

    out["min"] = np.nanmin(members, axis=1)
    out["max"] = np.nanmax(members, axis=1)

    out["q25"] = np.nanpercentile(members, 25, axis=1)
    out["q75"] = np.nanpercentile(members, 75, axis=1)
    out["iqr"] = out["q75"] - out["q25"]

    out["p005"] = np.nanquantile(members, lower_q, axis=1)
    out["p995"] = np.nanquantile(members, upper_q, axis=1)

    if envelope == "minmax":
        out["lb"] = out["min"]
        out["ub"] = out["max"]
    else:
        out["lb"] = out["p005"]
        out["ub"] = out["p995"]

    out["envelope"] = envelope
    out["lower_q"] = lower_q if envelope == "quantile" else np.nan
    out["upper_q"] = upper_q if envelope == "quantile" else np.nan
    out["n_members"] = np.sum(~np.isnan(members), axis=1)

    return out


def merge_summary_with_obs(
    summary: pd.DataFrame,
    obs: pd.Series,
    obs_col_name: str = "obs",
) -> pd.DataFrame:
    """Left-merge ensemble summary with a monthly observation series."""
    merged = summary.copy()

    if obs is None or obs.empty:
        merged[obs_col_name] = np.nan
        return merged

    obs_df = obs.rename(obs_col_name).to_frame().reset_index()
    obs_df.columns = ["datetime", obs_col_name]

    merged = merged.merge(obs_df, on="datetime", how="left")
    return merged