"""Extract monthly ensemble tables from CLM5 daily NetCDF history files.

For every (experiment, site) the extraction stage produces one wide CSV per
variable laid out as::

    datetime,real_0,real_1,...,real_127

Later pipeline stages operate purely on these CSVs; no NetCDF reads are
required downstream.

All CLM5 history files for a site are opened once, keeping only the required
scalar variables plus H2OSOI for soil moisture. Data are concatenated per
ensemble member, unit-scaled, resampled to monthly means, and pivoted to the
wide format described above.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import xarray as xr

from ..config import (
    ALL_VARIABLES,
    MONTHLY_RESAMPLE_FREQ,
    N_ENSEMBLE,
    VARIABLES,
    experiment_site_dir,
    intermediate_path,
)
from . import derive, io

log = logging.getLogger(__name__)

# Scalar output variables for this mode (no levsoi dimension).
# Derived from ALL_VARIABLES so SP-mode exclusions (e.g., NEE) are automatic.
_SCALAR_OUT_VARS: list[str] = [
    v for v in ALL_VARIABLES if not VARIABLES[v]["has_levsoi"]
]

# Raw NetCDF variable names to request from each history file.
# Uses sim_var so the SP override "FPSN" (for GPP) is picked up automatically.
# Deduplicated via dict.fromkeys to preserve insertion order.
# H2OSOI is appended separately — it requires levsoi slicing downstream.
_NC_VARS: list[str] = list(dict.fromkeys(
    VARIABLES[v]["sim_var"] for v in _SCALAR_OUT_VARS
)) + ["H2OSOI"]


def _member_to_dataframe(ds: xr.Dataset, site: str) -> pd.DataFrame:
    """Convert one member's xarray dataset to a DataFrame of our variables."""
    time = ds["time"].values.astype("datetime64[ns]")
    df = pd.DataFrame({"datetime": time})

    # Scalar variables — iterate over the mode-filtered list so that:
    #   - NEE is skipped in SP mode (not in _SCALAR_OUT_VARS)
    #   - GPP reads from "FPSN" in SP mode (VARIABLES["GPP"]["sim_var"] override)
    for out_var in _SCALAR_OUT_VARS:
        sim_var = VARIABLES[out_var]["sim_var"]
        scale = VARIABLES[out_var]["scale"]
        df[out_var] = np.ravel(ds[sim_var].values) * scale

    # Soil moisture -- two derived columns.
    if "H2OSOI" in ds:
        sm  = derive.surface_soil_moisture(ds["H2OSOI"], site)
        smr = derive.root_zone_soil_moisture(ds["H2OSOI"], site)
        df["SM"]  = np.ravel(sm.values)
        df["SMR"] = np.ravel(smr.values)
    else:
        df["SM"] = np.nan
        df["SMR"] = np.nan
    return df


def _monthly_ensemble_wide(members: dict[int, pd.DataFrame],
                           variable: str) -> pd.DataFrame:
    """Pivot {member_id: daily_df} → wide monthly DataFrame for ``variable``."""
    pieces: list[pd.DataFrame] = []
    for member_id in sorted(members):
        daily = members[member_id][["datetime", variable]].copy()
        monthly = io.timeseries_custom_resample(daily, "datetime", MONTHLY_RESAMPLE_FREQ,)
        monthly = monthly.rename(columns={variable: f"real_{member_id}"})
        pieces.append(monthly.set_index("datetime"))
    if not pieces:
        return pd.DataFrame()
    wide = pd.concat(pieces, axis=1)
    # Guarantee a stable column order.
    cols = [f"real_{i}" for i in range(max(members) + 1) if f"real_{i}" in wide]
    wide = wide[cols].reset_index()
    return wide


def extract_site(experiment: str,
                 site: str,
                 variables: Iterable[str] | None = None,
                 force: bool = False) -> dict[str, Path]:
    """Extract all variables for one (experiment, site) pair.

    Returns a dict {variable: csv_path}.  If ``force`` is False and all
    expected CSVs already exist, the NetCDF read is skipped.
    """
    variables = list(variables or ALL_VARIABLES)
    out_paths = {v: intermediate_path(experiment, site, v) for v in variables}

    if not force and all(p.exists() for p in out_paths.values()):
        log.info("Skipping %s/%s: intermediates already present", experiment, site)
        return out_paths

    src_dir = experiment_site_dir(experiment, site)
    log.info("Loading NetCDFs from %s", src_dir)
    datasets = io.load_ens_sim(src_dir, _NC_VARS)
    if not datasets:
        log.error("No ensemble files for %s/%s", experiment, site)
        return {}

    # Convert each member to a per-day dataframe of all our variables.
    member_dfs: dict[int, pd.DataFrame] = {}
    for key, ds in datasets.items():
        member_id = int(key.split("_", 1)[1])
        member_dfs[member_id] = _member_to_dataframe(ds, site)
        ds.close()

    # Write one wide CSV per variable.
    written: dict[str, Path] = {}
    for var in variables:
        wide = _monthly_ensemble_wide(member_dfs, var)
        if wide.empty:
            log.warning("Empty output for %s/%s/%s", experiment, site, var)
            continue
        path = out_paths[var]
        io.write_csv(wide, path)
        log.info("Wrote %s (%d rows, %d members)", path,
                 len(wide), wide.shape[1] - 1)
        written[var] = path

    return written


def extract_experiment(experiment: str,
                       sites: Iterable[str],
                       variables: Iterable[str] | None = None,
                       force: bool = False) -> dict[str, dict[str, Path]]:
    """Extract all sites for a given experiment."""
    out: dict[str, dict[str, Path]] = {}
    for site in sites:
        try:
            out[site] = extract_site(experiment, site, variables, force=force)
        except Exception as exc:
            log.exception("extract_site failed for %s/%s: %s",
                          experiment, site, exc)
            out[site] = {}
    return out
