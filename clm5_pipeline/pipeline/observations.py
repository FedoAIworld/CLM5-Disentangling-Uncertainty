"""Monthly observation loaders.

Inputs
------
all_obs_data.csv          time=YYYYMM, columns like ``{site}_{obs_col}``
all_surface_swc_mm.csv    time=YYYY-MM-DD, columns ``{site}_SM``
all_sm_root_mm.csv        time=YYYY-MM-DD, columns ``{site}_SMR``
LAI_ICOS/{site}_LAI_data_extracted.csv   Date, LAI_Mean, LAI_StdDev ...

The loaders expose a uniform interface: ``get_series(site, variable)``
returns a ``pd.Series`` whose timestamps match the monthly boundary
convention defined by ``MONTHLY_RESAMPLE_FREQ`` in config.py:

  * ``"MS"``       → first day of each month  (month-start)
  * ``"M"``/``"ME"`` → last  day of each month  (month-end)

This must agree with the model intermediate CSVs so that
``merge_summary_with_obs`` can join on ``datetime``.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from ..config import (
    MONTHLY_RESAMPLE_FREQ,
    OBS_FLUX_CSV,
    OBS_LAI_DIR,
    OBS_SMR_CSV,
    OBS_SM_CSV,
    OBS_UNAVAILABLE_SITES,
    VARIABLES,
)

log = logging.getLogger(__name__)

# True when the pipeline uses month-end timestamps ("M" or "ME").
_MONTH_END: bool = MONTHLY_RESAMPLE_FREQ in ("M", "ME")

# Pandas resample rule for LAI resampling — must match the model convention.
_LAI_RESAMPLE_RULE: str = "M" if _MONTH_END else "MS"


def _snap_to_month_boundary(dt_series: pd.Series) -> pd.Series:
    """Snap timestamps to the same month boundary as the model output.

    Month-end: snap any date within the month to the last day.
    Month-start: already at period-start after ``to_period().to_timestamp()``.
    """
    if _MONTH_END:
        return dt_series + pd.offsets.MonthEnd(0)
    return dt_series


# ---------------------------------------------------------------------------
# Flux CSV  (ET, H, NEE, GPP + RANDUNC / QC columns)
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def load_flux_obs() -> pd.DataFrame:
    if not Path(OBS_FLUX_CSV).exists():
        log.warning("Flux obs file not found at %s", OBS_FLUX_CSV)
        return pd.DataFrame()
    df = pd.read_csv(OBS_FLUX_CSV)
    # Handle BOM that exists on the "time" header.
    df.columns = [c.lstrip("\ufeff") for c in df.columns]
    # Parse YYYYMM → first-of-month, then snap to the pipeline's boundary.
    dt = pd.to_datetime(df["time"].astype(str), format="%Y%m")
    df["datetime"] = _snap_to_month_boundary(dt)
    df = df.drop(columns=["time"]).set_index("datetime").sort_index()
    # Replace -9999 sentinel with NaN.
    df = df.replace(-9999, np.nan)
    return df


@lru_cache(maxsize=1)
def load_sm_obs() -> pd.DataFrame:
    if not Path(OBS_SM_CSV).exists():
        log.warning("SM obs file not found at %s", OBS_SM_CSV)
        return pd.DataFrame()
    df = pd.read_csv(OBS_SM_CSV, parse_dates=["time"])
    df = df.rename(columns={"time": "datetime"})
    # Snap to the same monthly boundary as the model intermediates.
    dt = df["datetime"].dt.to_period("M").dt.to_timestamp()
    df["datetime"] = _snap_to_month_boundary(dt)
    return df.set_index("datetime").sort_index()


@lru_cache(maxsize=1)
def load_smr_obs() -> pd.DataFrame:
    if not Path(OBS_SMR_CSV).exists():
        log.warning("SMR obs file not found at %s", OBS_SMR_CSV)
        return pd.DataFrame()
    df = pd.read_csv(OBS_SMR_CSV, parse_dates=["time"])
    df = df.rename(columns={"time": "datetime"})
    dt = df["datetime"].dt.to_period("M").dt.to_timestamp()
    df["datetime"] = _snap_to_month_boundary(dt)
    return df.set_index("datetime").sort_index()


def load_lai_obs(site: str) -> pd.DataFrame:
    """Per-site LAI dataframe with ``datetime`` and ``LAI_Mean`` columns."""
    base = Path(OBS_LAI_DIR)
    
    candidates = [
        base / f"{site}_LAI_climatology.csv",      # SP mode
        base / f"{site}_LAI_data_extracted.csv",   # BGC mode
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return pd.DataFrame(columns=["datetime", "LAI_Mean", "LAI_StdDev"])
    df = pd.read_csv(path, parse_dates=["Date"])
    df = df.rename(columns={"Date": "datetime"})
    keep = [c for c in ("datetime", "LAI_Mean", "LAI_StdDev") if c in df.columns]
    return df[keep].sort_values("datetime").reset_index(drop=True)


# ---------------------------------------------------------------------------
# Uniform accessor
# ---------------------------------------------------------------------------
def get_obs_series(site: str, variable: str) -> Optional[pd.Series]:
    """Return the monthly observation series for (site, variable) or None."""
    obs_col = VARIABLES[variable]["obs_col"]

    # Honour the per-variable site exclusion table first.
    if site in OBS_UNAVAILABLE_SITES.get(variable, set()):
        return None

    if variable in ("ET", "H", "NEE", "GPP"):
        df = load_flux_obs()
        col = f"{site}_{obs_col}"
        if col not in df.columns:
            return None
        return df[col].rename(f"{site}_{variable}")

    if variable == "SM":
        df = load_sm_obs()
        col = f"{site}_SM"
        if col not in df.columns:
            return None
        return df[col].rename(f"{site}_SM")

    if variable == "SMR":
        df = load_smr_obs()
        col = f"{site}_SMR"
        if col not in df.columns:
            return None
        return df[col].rename(f"{site}_SMR")

    if variable == "TLAI":
        lai = load_lai_obs(site)
        if lai.empty:
            return None
        # Aggregate to monthly means using the same boundary as the model.
        monthly = (lai.set_index("datetime")["LAI_Mean"]
                      .resample(_LAI_RESAMPLE_RULE).mean())
        return monthly.rename(f"{site}_TLAI")

    return None


def get_lai_monthly_climatology(site: str) -> pd.DataFrame:
    """Monthly LAI climatology (mean ± RMS of LAI_StdDev) for TLAI plotting.

    For each calendar month, ``obs_mean`` is the mean of LAI_Mean across all
    observations in that month and ``obs_std`` is the root-mean-square of the
    per-observation LAI_StdDev values. Falls back to the inter-year standard
    deviation of monthly means when LAI_StdDev is unavailable.

    Returns
    -------
    DataFrame with columns ``month`` (1-12), ``obs_mean``, ``obs_std``.
    An empty DataFrame is returned when no LAI data exists for the site.
    """
    lai = load_lai_obs(site)
    if lai.empty:
        return pd.DataFrame(columns=["month", "obs_mean", "obs_std"])

    lai = lai.copy()
    lai["month"] = pd.to_datetime(lai["datetime"]).dt.month

    if "LAI_StdDev" in lai.columns:
        grp = lai.groupby("month")
        obs_mean = grp["LAI_Mean"].mean()
        # RMS of per-observation standard deviations within each month.
        obs_std  = grp["LAI_StdDev"].apply(lambda x: float(np.sqrt(np.mean(x ** 2))))
    else:
        grp      = lai.groupby("month")["LAI_Mean"]
        obs_mean = grp.mean()
        obs_std  = grp.std()

    return pd.DataFrame({
        "month":    obs_mean.index.tolist(),
        "obs_mean": obs_mean.values,
        "obs_std":  obs_std.values,
    })


def get_obs_uncertainty(site: str, variable: str) -> Optional[pd.Series]:
    """Return a RANDUNC series (1-sigma) for flux variables if available."""
    df = load_flux_obs()
    if df.empty:
        return None
    if variable == "NEE":
        col = f"{site}_NEE_VUT_REF_RANDUNC"
    elif variable == "H":
        col = f"{site}_H_RANDUNC"
    elif variable == "ET":
        # ET not directly given; can be approximated from LE_RANDUNC.
        col = f"{site}_LE_RANDUNC"
        if col not in df.columns:
            return None
        # 0.035 W m^-2 → mm d^-1 conversion factor for latent heat.
        return (df[col] * 0.035).rename(f"{site}_{variable}_RANDUNC")
    elif variable == "GPP":
        return None
    else:
        return None
    if col not in df.columns:
        return None
    return df[col].rename(f"{site}_{variable}_RANDUNC")


def obs_time_index(site: str, variable: str) -> pd.DatetimeIndex:
    """Return the datetime index where observations are not NaN."""
    s = get_obs_series(site, variable)
    if s is None:
        return pd.DatetimeIndex([])
    return s.dropna().index


# ---------------------------------------------------------------------------
# Debug helpers
# ---------------------------------------------------------------------------
def summarise_availability(sites: Iterable[str], variables: Iterable[str]) -> pd.DataFrame:
    """Matrix of observation count per (site, variable)."""
    records = []
    for site in sites:
        row = {"site": site}
        for var in variables:
            s = get_obs_series(site, var)
            row[var] = 0 if s is None else int(s.dropna().size)
        records.append(row)
    return pd.DataFrame(records)
