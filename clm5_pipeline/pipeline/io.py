"""NetCDF / CSV helpers.

Provides functions for loading CLM5 ensemble NetCDF files, converting
xarray datasets to DataFrames, resampling to monthly frequency, and
reading/writing the wide ensemble CSV format (``datetime`` + ``real_0 ...
``real_127``).
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

import numpy as np
import pandas as pd
import xarray as xr

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NetCDF loading
# ---------------------------------------------------------------------------
_FN_REGEX = re.compile(r"clmoas\.clm2_(\d+)\.h0\.(\d{4})-\d{2}-\d{2}-\d+\.nc$")


def _preprocess(ds: xr.Dataset, clm_vars: Sequence[str]) -> xr.Dataset:
    """Keep only the variables of interest and drop everything else."""
    missing = [v for v in clm_vars if v not in ds.variables]
    if missing:
        raise KeyError(f"Variables {missing} missing from NetCDF file")
    return ds[list(clm_vars)]


def list_ensemble_files(directory: Path | str) -> List[Path]:
    """Return all ``clmoas.clm2_*.h0.YYYY-MM-DD-00000.nc`` files sorted."""
    d = Path(directory)
    if not d.exists():
        raise FileNotFoundError(f"Ensemble directory not found: {d}")
    files = sorted(p for p in d.iterdir()
                   if p.is_file() and _FN_REGEX.match(p.name))
    return files


def parse_member_year(filename: str) -> tuple[int, int] | None:
    m = _FN_REGEX.match(filename)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def load_ens_sim(directory: Path | str,
                 clm_vars: Sequence[str]) -> Dict[str, xr.Dataset]:
    """Load ensemble simulation files and concatenate per realization.

    Returns {"real_0": ds, "real_1": ds, ...} with time concatenated
    chronologically for each ensemble member.
    """
    files = list_ensemble_files(directory)
    if not files:
        log.warning("No matching NetCDF files found in %s", directory)
        return {}

    buckets: Dict[int, List[xr.Dataset]] = {}
    for f in files:
        parsed = parse_member_year(f.name)
        if parsed is None:
            continue
        member, _year = parsed
        try:
            ds = xr.open_dataset(f, decode_times=True)
        except Exception as exc:  # pragma: no cover - IO failures
            log.error("Failed to open %s: %s", f, exc)
            continue
        ds = _preprocess(ds, clm_vars)
        buckets.setdefault(member, []).append(ds)

    out: Dict[str, xr.Dataset] = {}
    for member in sorted(buckets):
        parts = sorted(buckets[member], key=lambda d: d.time.values[0])
        out[f"real_{member}"] = xr.concat(parts, dim="time")
    return out


# ---------------------------------------------------------------------------
# DataFrame conversion / resampling
# ---------------------------------------------------------------------------
def convert_ens_to_dataframe(dataset: Dict[str, xr.Dataset],
                             var_list: Sequence[str]) -> Dict[int, pd.DataFrame]:
    """Convert each realization's xarray dataset to a pandas DataFrame.

    The returned dict keys are realization integers so they are easy to sort
    / iterate.  Each DataFrame has a ``datetime`` column and one column per
    variable in ``var_list``.
    """
    dfs: Dict[int, pd.DataFrame] = {}
    for key, ds in dataset.items():
        if not key.startswith("real_"):
            continue
        realization = int(key.split("_", 1)[1])
        time = ds["time"].values.astype("datetime64[ns]")
        df = pd.DataFrame({"datetime": time})
        for var in var_list:
            # Keep a 1-D view if the variable is already scalar-per-time.
            arr = np.ravel(ds[var].values)
            if arr.size == time.size:
                df[var] = arr
            else:
                # For multi-dim vars (e.g., H2OSOI with levsoi) stash the whole
                # array so the caller can slice levsoi later.
                df[var] = list(ds[var].values)
        dfs[realization] = df
    return dfs


def timeseries_custom_resample(df: pd.DataFrame,
                               datetime_col: str = "datetime",
                               freq: str = "MS") -> pd.DataFrame:
    """Resample a time-indexed dataframe at ``freq`` taking the mean."""
    df = df.set_index(datetime_col).resample(freq).mean(numeric_only=True)
    return df.reset_index()


# ---------------------------------------------------------------------------
# Common CSV helpers
# ---------------------------------------------------------------------------
def read_wide_ensemble_csv(path: Path | str) -> pd.DataFrame:
    """Read a ``datetime, real_0 ... real_N`` CSV produced by extract.py."""
    df = pd.read_csv(path, parse_dates=["datetime"])
    df["datetime"] = pd.to_datetime(df["datetime"])
    return df


def write_csv(df: pd.DataFrame, path: Path | str) -> Path:
    """Write ``df`` to ``path`` creating parent dirs along the way."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False)
    return p
