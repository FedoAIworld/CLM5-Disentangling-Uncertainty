#!/usr/bin/env python3
"""Central configuration for the CLM5 ensemble evaluation pipeline.

Everything that tends to change between machines or experiments lives here.
Paths default to the JSC scratch layout described in the project brief but
can be overridden via environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Pipeline mode  (BGC = full 4-experiment run; SP = single-experiment subset)
# ---------------------------------------------------------------------------
# Override at runtime via the environment variable or the --mode CLI flag.
PIPELINE_MODE: str = os.environ.get("CLM5_PIPELINE_MODE", "bgc").lower()
if PIPELINE_MODE not in ("bgc", "sp"):
    raise ValueError(
        f"CLM5_PIPELINE_MODE must be 'bgc' or 'sp', got {PIPELINE_MODE!r}"
    )

# ---------------------------------------------------------------------------
# Sites
# ---------------------------------------------------------------------------
SITES_BGC = [
    "FI-Hyy", "FI-Sod", "SE-Svb", "CZ-BK1", "DE-Obe", "DE-RuW",
    "IT-Lav", "NL-Loo", "ES-Cnd", "FR-Pue", "DE-Hai", "DE-HoH",
    "DK-Vng", "BE-Bra",
]

SITES_SP = [
    "FI-Hyy", "SE-Svb", "CZ-BK1", "DE-RuW",
    "NL-Loo", "FR-Pue", "DE-Hai", "DE-HoH", "BE-Bra",
]

# Active site list for the current mode.
SITES = SITES_BGC if PIPELINE_MODE == "bgc" else SITES_SP

SITE_FULL = [
    "FI-Hyytiälä", "FI-Sodankylä", "SE-Svartberget", "CZ-Bily Kriz",
    "DE-Oberbärenburg", "DE-Wüstebach", "IT-Lavarone", "NL-Loobos",
    "ES-Conde", "FR-Puechabon", "DE-Hainich", "DE-Hohes Holz",
    "DK-Voulund", "BE-Brasschaat",
]

SITE_FULL_NAME = dict(zip(SITES_BGC, SITE_FULL))

SITE_PFT = {
    "FI-Hyy": "ENF", "FI-Sod": "ENF", "SE-Svb": "ENF",
    "CZ-BK1": "ENF", "DE-Obe": "ENF", "DE-RuW": "ENF",
    "IT-Lav": "ENF", "NL-Loo": "ENF",
    "ES-Cnd": "EBF", "FR-Pue": "EBF",
    "DE-Hai": "DBF", "DE-HoH": "DBF",
    "DK-Vng": "CRO", "BE-Bra": "MF",
}

# ---------------------------------------------------------------------------
# Experiments
# ---------------------------------------------------------------------------
EXPERIMENTS_BGC = ["forcing", "soil", "vegetation", "combined"]
EXPERIMENTS_SP  = ["combined"]

# Active experiment list for the current mode.
EXPERIMENTS = EXPERIMENTS_BGC if PIPELINE_MODE == "bgc" else EXPERIMENTS_SP

EXPERIMENT_LABEL = {
    "forcing":    "Perturbed atmospheric forcing",
    "soil":       "Perturbed soil parameters",
    "vegetation": "Perturbed vegetation parameters",
    "combined":   "Combined perturbation",
}

# Bar / line colours used by all composite figure helpers.
EXPERIMENT_COLORS = {
    "forcing":    "#3182bd",
    "soil":       "#9ecae1",
    "vegetation": "#2ca25f",
    "combined":   "#FF0000",
}

N_ENSEMBLE = 128
ENSEMBLE_REAL_IDS = list(range(N_ENSEMBLE))

# Analysis window
PERIOD_START = "2009-01-01"
PERIOD_END   = "2018-12-31"
GROWING_MONTHS = list(range(4, 11))  # April-October

# Seasonal grouping used by the sigma-bar composite (Figure 8).
SEASON_ORDER  = ["Spring", "Summer", "Fall", "Winter"]
SEASON_MONTHS = {
    "Spring": [3, 4, 5],
    "Summer": [6, 7, 8],
    "Fall":   [9, 10, 11],
    "Winter": [12, 1, 2],
}

# ---------------------------------------------------------------------------
# CLM variables and observation mapping
# ---------------------------------------------------------------------------
# Key: short variable used throughout the pipeline.
# sim_var    - original CLM5 variable in the NetCDF files.
# obs_col    - matching column suffix in all_obs_data.csv / ancillary files.
# label      - human label used on plots.
# unit       - unit string for y-axis.
# scale      - multiplicative factor applied to raw sim data (per-day etc).
# has_levsoi - whether the variable requires LEVSOI slicing (H2OSOI).
VARIABLES = {
    "ET":   {"sim_var": "QFLX_EVAP_TOT", "obs_col": "ET",            "label": "ET",   "unit": " (mm d$^{-1}$)",         "scale": 86400.0, "has_levsoi": False},
    "H":    {"sim_var": "FSH",           "obs_col": "H_F_MDS",       "label": "H",    "unit": " (W m$^{-2}$)",          "scale": 1.0,     "has_levsoi": False},
    "NEE":  {"sim_var": "NEE",           "obs_col": "NEE_VUT_REF",   "label": "NEE",  "unit": " (gC m$^{-2}$ d$^{-1}$)","scale": 86400.0, "has_levsoi": False},
    "GPP":  {"sim_var": "GPP",           "obs_col": "GPP_NT_VUT_REF","label": "GPP",  "unit": " (gC m$^{-2}$ d$^{-1}$)","scale": 86400.0, "has_levsoi": False},
    "TLAI": {"sim_var": "TLAI",          "obs_col": "LAI_Mean",      "label": "TLAI", "unit": " (m$^{2}$ m$^{-2}$)",    "scale": 1.0,     "has_levsoi": False},
    "SM":   {"sim_var": "H2OSOI",        "obs_col": "SM",            "label": "SM",   "unit": " (%)",                   "scale": 100.0,   "has_levsoi": True},
    "SMR":  {"sim_var": "H2OSOI",        "obs_col": "SMR",           "label": "SMR",  "unit": " (%)",                   "scale": 100.0,   "has_levsoi": True},
}

# ---------------------------------------------------------------------------
# SP mode variable overrides
# CLM5-SP history files differ from BGC:
#   - GPP is not written; FPSN (photosynthesis) is used as a proxy.
#   - NEE is not written and must be excluded from the evaluation.
# ---------------------------------------------------------------------------
if PIPELINE_MODE == "sp":
    # FPSN units: µmol CO₂ m⁻² s⁻¹  →  gC m⁻² d⁻¹
    # scale = 12.011 g mol⁻¹  ×  86400 s d⁻¹  ×  1×10⁻⁶ mol µmol⁻¹
    _FPSN_SCALE = 12.011 * 86400.0 * 1e-6   # ≈ 1.03775 gC m⁻² d⁻¹ per µmol m⁻² s⁻¹
    VARIABLES["GPP"] = {**VARIABLES["GPP"], "sim_var": "FPSN", "scale": _FPSN_SCALE}

# Variable mapping.
VARIABLE_MAP = {k: v["sim_var"] for k, v in VARIABLES.items()}
ALL_VARIABLES = list(VARIABLES.keys())

# Variables included for model-vs-obs time-series plots.
OBS_VARIABLES = ["ET", "H", "NEE", "GPP", "SM", "SMR"]

# SP mode: NEE is absent from CLM5-SP history files.
if PIPELINE_MODE == "sp":
    ALL_VARIABLES  = [v for v in ALL_VARIABLES  if v != "NEE"]
    OBS_VARIABLES  = [v for v in OBS_VARIABLES  if v != "NEE"]

CLIMATOLOGY_VARIABLES = ALL_VARIABLES  # TLAI included

# ---------------------------------------------------------------------------
# Soil layer indices (levsoi is 0-based in xarray after isel).
# ---------------------------------------------------------------------------
LEVSOI_MAP = {
    "default": {
        "sm_5cm":  [1],
        "sm_20cm": [3],
        "sm_50cm": [6],
    },
}

# Root-zone soil moisture weights: 20 % at 5 cm, 40 % at 20 cm, 40 % at 50 cm.
# Fractions sum to 1.0, so:
# SMR = 0.20·SM_5cm + 0.40·SM_20cm + 0.40·SM_50cm (before ×100 % conversion).
SMR_LAYER_WEIGHTS = {"sm_5cm": 0.20, "sm_20cm": 0.40, "sm_50cm": 0.40}

# Per-variable site exclusions: sites for which no in-situ obs limited/corrupt.
# Used by observations.get_obs_series(), composite filters, and the metrics runner.
OBS_UNAVAILABLE_SITES: dict[str, set] = {
    "SM":  {"FI-Sod", "ES-Cnd", "SE-Svb"},   # no/limited/incorrect in-situ soil-moisture sensors
    "SMR": {"FI-Sod", "ES-Cnd", "SE-Svb"},   # same sites
    "H":   {"DE-RuW"},                       # sensible-heat flux suspicious/unavailable
    "GPP": {"ES-Cnd", "DK-Vng"},             # GPP obs not available for these sites
}

SM_SMR_UNAVAILABLE_SITES: set = OBS_UNAVAILABLE_SITES["SM"]

MONTHLY_RESAMPLE_FREQ = "M"           # "MS" = month-start  |  "M" = month-end
# NOTE: "ME" (pandas ≥ 2.2 alias) is NOT valid on JSC (SciPy-bundle 2023.07 /
# pandas ~2.0).  Use "M" for month-end on that cluster.

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
MODEL_BASE_DIR = Path(os.environ.get(
    "CLM5_MODEL_BASE_DIR",
    "/p/scratch/cjicg41/eloundou1/CLM5_DATA/Archive/lnd/hist/Ensemble",
))

EXPERIMENT_DIR = {exp: MODEL_BASE_DIR / exp for exp in EXPERIMENTS}

# Default observation directory on JSC.  Falls back to the workspace copy
# if the scratch path is not visible (e.g., when running locally for tests).
_DEFAULT_OBS_DIR = "/p/scratch/cjicg41/eloundou1/Observations/ICOS_data"
OBS_DIR = Path(os.environ.get("CLM5_OBS_DIR", _DEFAULT_OBS_DIR))
if not OBS_DIR.exists():
    # Local developer convenience.
    _local_obs = Path(__file__).resolve().parent.parent / "Datasets" / "obs_data"
    if _local_obs.exists():
        OBS_DIR = _local_obs

OBS_FLUX_CSV = OBS_DIR / "all_obs_data.csv"
OBS_SM_CSV   = OBS_DIR / "all_surface_swc_mm.csv"
OBS_SMR_CSV  = OBS_DIR / "all_sm_root_mm.csv"
# SP mode uses a pre-computed LAI climatology; BGC uses the full ICOS time series.
OBS_LAI_DIR  = OBS_DIR / ("LAI_obs_climatology" if PIPELINE_MODE == "sp" else "LAI_ICOS")

# Output layout - everything below a single root.
OUTPUT_ROOT = Path(os.environ.get(
    "CLM5_EVAL_OUTPUT_ROOT",
    str(MODEL_BASE_DIR / "evaluation_sp"),
))

OUTPUT_DIRS = {
    "intermediates": OUTPUT_ROOT / "intermediates",
    "plot_inputs":   OUTPUT_ROOT / "plot_inputs",
    "metrics":       OUTPUT_ROOT / "metrics",
    "figures":       OUTPUT_ROOT / "figures",
    "logs":          OUTPUT_ROOT / "logs",
}

# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
FIGURE_FAMILIES = {
    "spread_vs_obs":          "A_spread_vs_obs",
    "iqr_mean_obs_spread":    "B_iqr_mean_obs_spread",
    "obs_mean_only":          "C_obs_mean_only",
    "climatology":            "D_climatology",
}

# Multi-site composite figures (one per experiment, or cross-experiment).
COMPOSITE_FAMILIES = {
    "composite_spread_vs_obs":          "E_composite_spread_vs_obs",
    "composite_spread_obs_unc":         "F_composite_spread_obs_unc",
    "composite_iqr_mean_obs_spread":    "G_composite_iqr_mean_obs_spread",
    "composite_climatology":            "H_composite_climatology",
    "all_experiments_grid":             "I_all_experiments",
    "coverage_heatmap":                 "J_coverage_heatmap",
    "ss_heatmap":                       "K_ss_heatmap",
    "seasonal_sigma_bars":              "L_seasonal_sigma_bars",
    "coverage_bars":                    "M_coverage_bars",
    "domain_heatmap":                   "N_domain_heatmap",
    "combined_coverage_domain":         "O_combined_coverage_domain",
}

# Shared rcParams applied to all per-site figures.
PLOT_STYLE = {
    "figure.dpi":         120,
    "savefig.dpi":        300,
    "font.size":          16,
    "axes.linewidth":     1.4,
    "grid.linewidth":     0.8,
    "xtick.major.width":  1.2,
    "ytick.major.width":  1.2,
    "xtick.major.size":   5,
    "ytick.major.size":   5,
}

# Per-variable y-limits for composite plots. Set a value to None to auto-scale.
YLIMITS = {
    "ET":  (-1.0,  8.0),
    "H":   (-110, 220),
    "NEE": (-12,   10),
    "GPP": (-0.5,  20),
    "SM":  (0,    100),
    "SMR": (0,    100),
    "TLAI":(0,    15),
}

# ---------------------------------------------------------------------------
# Runtime
# ---------------------------------------------------------------------------
# Ensemble envelope used for summary["lb"] and summary["ub"].
#
# "minmax"   -> lb/ub = ensemble min/max
# "quantile" -> lb/ub = lower/upper quantiles, usually 0.005/0.995
#
# This controls both CP and composite spread plots, because both use lb/ub.
ENSEMBLE_ENVELOPE = "minmax"

# Quantile bounds used only when ENSEMBLE_ENVELOPE = "quantile".
ENVELOPE_LOWER_Q = 0.005
ENVELOPE_UPPER_Q = 0.995

# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------
def ensure_output_dirs():
    """Create the top-level output directories if they don't already exist."""
    for path in OUTPUT_DIRS.values():
        path.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIRS


def experiment_site_dir(experiment: str, site: str) -> Path:
    """Return the NetCDF source directory for a (experiment, site) pair."""
    return EXPERIMENT_DIR[experiment] / site


def intermediate_path(experiment: str, site: str, variable: str) -> Path:
    """Wide ensemble CSV produced by the extraction stage."""
    return (
        OUTPUT_DIRS["intermediates"]
        / experiment
        / variable
        / f"{site}_{variable}_ensemble.csv"
    )


def plot_input_path(experiment: str, site: str, variable: str, kind: str) -> Path:
    """CSV tables consumed by the plotting stage.

    kind ∈ {"summary", "merged", "climatology"}.
    """
    return (
        OUTPUT_DIRS["plot_inputs"]
        / experiment
        / variable
        / f"{site}_{variable}_{kind}.csv"
    )


def metric_path(experiment: str, variable: str, scope: str = "all") -> Path:
    """CSV where per-site metrics for a (experiment, variable) are stored.

    scope ∈ {"all", "growing"}.
    """
    return (
        OUTPUT_DIRS["metrics"]
        / experiment
        / f"metrics_{variable}_{scope}.csv"
    )


def figure_path(family: str, experiment: str, variable: str, site: str, ext: str) -> Path:
    fam_dir = FIGURE_FAMILIES[family]
    return (
        OUTPUT_DIRS["figures"]
        / fam_dir
        / experiment
        / variable
        / f"{site}_{variable}_{fam_dir}.{ext}"
    )


def composite_figure_path(family: str, variable: str, ext: str,
                          experiment: str | None = None,
                          scope: str = "all") -> Path:
    """Output path for a multi-site composite figure.

    experiment is None for cross-experiment figures.
    scope is "all" or "growing" for heatmap / coverage-bar variants.
    """
    fam_dir = COMPOSITE_FAMILIES[family]
    base = OUTPUT_DIRS["figures"] / fam_dir
    # ── heatmaps keyed by experiment + scope ──────────────────────────────
    if family in ("coverage_heatmap", "ss_heatmap"):
        fname = f"{family}_{experiment or 'combined'}_{scope}.{ext}"
        return base / fname
    # ── new figure families ───────────────────────────────────────────────
    if family == "seasonal_sigma_bars":
        # One single figure (all variables in a 2×3 grid).
        return base / f"seasonal_sigma_bars.{ext}"
    if family == "coverage_bars":
        # Single figure with both scopes as rows — no scope suffix.
        return base / f"coverage_bars.{ext}"
    if family == "domain_heatmap":
        fname = f"domain_heatmap_{experiment or 'combined'}_{scope}.{ext}"
        return base / fname
    if family == "combined_coverage_domain":
        fname = f"combined_coverage_domain_{experiment or 'combined'}_{scope}.{ext}"
        return base / fname
    # ── standard per-experiment/variable families ──────────────────────────
    if experiment is None:
        fname = f"{family}_{variable}_all_experiments.{ext}"
        return base / variable / fname
    fname = f"{family}_{experiment}_{variable}.{ext}"
    return base / experiment / variable / fname
