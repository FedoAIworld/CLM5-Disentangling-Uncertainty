"""Monthly climatology helpers.

The pipeline produces two flavours of climatologies:

* Model-only: for TLAI, and as a fallback for any variable where no
  observation exists for the site.
* Model + observations: whenever a paired observation series is available.

The returned dataframe always has a ``month`` column (1-12) plus
``mean``, ``q25``, ``q75``, ``min``, ``max`` (ensemble aggregates averaged
across years) and, when available, ``obs_mean`` / ``obs_std`` from the
observation series.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd


_MEMBER_PREFIX = "real_"


def ensemble_member_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(_MEMBER_PREFIX)]


def model_climatology(members_df: pd.DataFrame) -> pd.DataFrame:
    """Return monthly climatology (mean / q25 / q75 / min / max) from members.

    The per-row mean, q25, q75, min, max are first computed across members,
    then averaged across years for each month.
    """
    cols = ensemble_member_cols(members_df)
    if not cols:
        raise ValueError("No 'real_*' columns in dataframe")

    matrix = members_df[cols].to_numpy(dtype=float)
    per_row = pd.DataFrame({
        "datetime": members_df["datetime"].values,
        "mean":   np.nanmean(matrix, axis=1),
        "q25":    np.nanpercentile(matrix, 25, axis=1),
        "q75":    np.nanpercentile(matrix, 75, axis=1),
        "min":    np.nanmin(matrix, axis=1),
        "max":    np.nanmax(matrix, axis=1),
    })
    per_row["month"] = per_row["datetime"].dt.month
    return (per_row.groupby("month")[["mean", "q25", "q75", "min", "max"]]
                    .mean()
                    .reset_index())


def observed_climatology(obs: pd.Series) -> pd.DataFrame:
    """Monthly mean / std of an observation series."""
    if obs is None or obs.empty:
        return pd.DataFrame(columns=["month", "obs_mean", "obs_std"])
    df = obs.rename("obs").to_frame()
    df["month"] = df.index.month
    grp = df.groupby("month")["obs"]
    return pd.DataFrame({
        "month":    grp.mean().index,
        "obs_mean": grp.mean().values,
        "obs_std":  grp.std().values,
    })


def climatology_table(members_df: pd.DataFrame,
                      obs: Optional[pd.Series],
                      obs_clim: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Combined climatology table ready for plotting / CSV export.

    Parameters
    ----------
    members_df : wide ensemble DataFrame.
    obs : observation Series (used when ``obs_clim`` is None).
    obs_clim : optional pre-computed monthly climatology DataFrame with
        columns ``month``, ``obs_mean``, ``obs_std``.  When supplied it
        takes precedence over computing the climatology from ``obs``.
        Used for TLAI where we want RMS(LAI_StdDev) rather than the
        inter-year standard deviation of monthly means.
    """
    model = model_climatology(members_df)
    # Always return all 12 months even if data is missing.
    model = (pd.DataFrame({"month": range(1, 13)})
               .merge(model, on="month", how="left"))
    if obs_clim is not None and not obs_clim.empty:
        # Use caller-supplied monthly stats (e.g., LAI RMS StdDev).
        return model.merge(obs_clim[["month", "obs_mean", "obs_std"]],
                           on="month", how="left")
    if obs is None or obs.empty:
        model["obs_mean"] = np.nan
        model["obs_std"] = np.nan
        return model
    obs_df = observed_climatology(obs)
    return model.merge(obs_df, on="month", how="left")
