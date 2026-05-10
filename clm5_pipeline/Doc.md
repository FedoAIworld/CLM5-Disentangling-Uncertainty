# CLM5 Ensemble Evaluation Pipeline

A Python pipeline for evaluating CLM5 ensemble simulations against ICOS eddy-covariance observations. Given an archive of CLM5 daily history NetCDF files, the pipeline derives monthly time series for every site, experiment, and ensemble member; computes evaluation metrics; and produces figures.

This code accompanies the manuscript:

> **[Disentangling Sources of Uncertainty in CLM5 Model Predictions: Water, Energy, and Carbon Fluxes at European Observation Sites]** — [Fernand B. Eloundou], *[JGR-Biogeosciences]*, [Year]. DOI: [doi]

---

## Overview

| Dimension   | Detail                                                   |
|-------------|----------------------------------------------------------|
| Experiments | 4 — `forcing`, `soil`, `vegetation`, `combined`          |
| Sites       | 14 ICOS sites (FI-Hyytiälä to BE-Brasschaat)             |
| Members     | 128 ensemble realisations (`real_0` … `real_127`)        |
| Period      | 2009–2018, monthly aggregates                            |
| Variables   | ET, H, NEE, GPP, TLAI, SM, SMR                           |

Variable definitions:

| Short name | CLM5 variable      | Transformation                                   |
|------------|--------------------|--------------------------------------------------|
| ET         | `QFLX_EVAP_TOT`    | × 86 400 → mm d⁻¹                                |
| H          | `FSH`              | W m⁻² (no scaling)                               |
| NEE        | `NEE`              | × 86 400 → gC m⁻² d⁻¹                            |
| GPP        | `GPP`              | × 86 400 → gC m⁻² d⁻¹                            |
| TLAI       | `TLAI`             | m² m⁻² (no scaling)                              |
| SM         | `H2OSOI[5 cm]`     | × 100 → %                                        |
| SMR        | `H2OSOI` weighted  | weighted mean of 5/20/50 cm layers × 100 → %     |

---

## Repository layout

```
clm5_pipeline/
├── config.py                 # sites, variables, paths, soil-layer indices
├── run_pipeline.py           # CLI entry point
├── verify_pipeline.py        # sanity checks (no NetCDFs required)
├── submit_jsc.sh             # SLURM array script (per-site jobs)
├── submit_jsc_aggregate.sh   # SLURM aggregation + composite job
└── pipeline/
    ├── io.py                 # NetCDF loading and CSV helpers
    ├── derive.py             # SM / SMR derivation from H2OSOI
    ├── extract.py            # NetCDF → monthly wide ensemble CSVs
    ├── observations.py       # observation loaders (flux, SM, SMR, LAI)
    ├── summaries.py          # ensemble statistics (mean/IQR/spread)
    ├── metrics.py            # CP, MBE, RMSE, ubRMSE, σ, SS
    ├── climatology.py        # monthly climatology tables
    ├── plotting.py           # per-site figure families A–D
    ├── composite.py          # multi-site composite families E–O
    └── runner.py             # pipeline orchestrator
```

---

## Requirements

Python 3.10 or later. Install dependencies with:

```bash
pip install numpy pandas xarray netCDF4 matplotlib seaborn
```

> **Note on pandas version**: The `MONTHLY_RESAMPLE_FREQ` setting in `config.py`
> controls the monthly timestamp boundary. Use `"M"` (month-end) on pandas < 2.2
> and `"ME"` on pandas ≥ 2.2. The default is `"M"`. Whatever value is set here,
> the observation loaders synchronise automatically.

---

## Input data

### CLM5 NetCDF archive

Files must follow the naming convention:

```
{model_base_dir}/{experiment}/{site}/clmoas.clm2_{NNNN}.h0.{YYYY}-{MM}-{DD}-00000.nc
```

where `NNNN` is the zero-padded ensemble member index (0000–0127). Each file
covers one calendar year of daily output and must contain the variables
`QFLX_EVAP_TOT`, `FSH`, `NEE`, `GPP`, `TLAI`, and `H2OSOI`.

### Observation files

Place observation CSVs in `$CLM5_OBS_DIR` (see [Configuration](#configuration)):

| File                                            | Contents                                            |
|-------------------------------------------------|-----------------------------------------------------|
| `all_obs_data.csv`                              | Monthly flux obs — columns `{site}_{variable}`      |
| `all_surface_swc_mm.csv`                        | Monthly surface soil moisture — columns `{site}_SM` |
| `all_sm_root_mm.csv`                            | Monthly root-zone soil moisture — `{site}_SMR`      |
| `LAI_ICOS/{site}_LAI_data_extracted.csv`        | Per-site LAI with `Date`, `LAI_Mean`, `LAI_StdDev`  |
| `LAI_obs_climatology/{site}_LAI_climatology.csv`| Per-site LAI with `Date`, `LAI_Mean`, `LAI_StdDev`  |

Missing observation files are handled gracefully — affected variables are
computed as model-only outputs.

---

## Configuration

All tunable parameters live in `config.py`. The most commonly adjusted settings:

| Name                    | Default           | Description                                         |
|-------------------------|-------------------|-----------------------------------------------------|
| `PERIOD_START`          | `"2009-01-01"`    | Start of the evaluation window                      |
| `PERIOD_END`            | `"2018-12-31"`    | End of the evaluation window                        |
| `GROWING_MONTHS`        | April–October     | Months used for growing-season metrics              |
| `MONTHLY_RESAMPLE_FREQ` | `"M"`             | Pandas resample rule — `"M"` or `"MS"`              |
| `N_ENSEMBLE`            | `128`             | Number of ensemble members                          |
| `LEVSOI_MAP`            | see file          | Soil-layer indices for SM/SMR per site              |
| `SMR_LAYER_WEIGHTS`     | 0.2/0.4/0.4       | Depth weights for the SMR weighted mean             |
| `OBS_UNAVAILABLE_SITES` | see file          | Sites excluded from specific variable metrics       |

Path defaults can be overridden via environment variables:

| Variable                | Default                                           |
|-------------------------|---------------------------------------------------|
| `CLM5_MODEL_BASE_DIR`   | `/p/scratch/.../Ensemble`                        |
| `CLM5_EVAL_OUTPUT_ROOT` | `${CLM5_MODEL_BASE_DIR}/evaluation`              |
| `CLM5_OBS_DIR`          | `/p/scratch/.../Observations/ICOS_data`          |

---

## Running the pipeline

### Verify installation (no NetCDFs needed)

```bash
python verify_pipeline.py
```

This checks imports, config constants, observation loaders, metric
calculations, plotting, and extraction against a synthetic NetCDF fixture.

### Single site

```bash
python run_pipeline.py --experiment forcing --site FI-Hyy
```

### Full experiment (all 14 sites)

```bash
python run_pipeline.py --experiment combined --workers 4
```

### All experiments and sites

```bash
python run_pipeline.py --all --workers 4
```

### Composite figures only (from cached CSVs)

```bash
python run_pipeline.py --composites-only
```

### Rerun incomplete site jobs, then aggregate and render composites

```bash
python run_pipeline.py --aggregate-only --repair-missing --workers 4
```

Key CLI flags:

| Flag                | Description                                            |
|---------------------|--------------------------------------------------------|
| `--force`           | Re-extract from NetCDF even if CSVs already exist      |
| `--no-plots`        | Skip per-site figure generation                        |
| `--with-composites` | Render composite figures after per-site processing     |
| `--repair-missing`  | Rerun jobs whose outputs are absent before aggregating |

---

## Running on a SLURM cluster

```bash
# This runs both all experiments on JSC machine.
batch submit_jsc_full.sh --mode sp
```
---

## Output layout

```
evaluation/
├── intermediates/
│   └── {experiment}/{variable}/{site}_{variable}_ensemble.csv
├── plot_inputs/
│   └── {experiment}/{variable}/{site}_{variable}_{summary|merged|climatology}.csv
├── metrics/
│   ├── {experiment}/{site}_metrics.csv
│   └── {experiment}/metrics_{variable}_{all|growing}.csv
├── figures/
│   ├── A_spread_vs_obs/             # ensemble spread + observation
│   ├── B_iqr_mean_obs_spread/       # IQR band + mean + spread + observation
│   ├── C_obs_mean_only/             # ensemble mean vs observation
│   ├── D_climatology/               # monthly climatology per site
│   ├── E_composite_spread_vs_obs/   # multi-site grid with CP/SS annotations
│   ├── F_composite_spread_obs_unc/  # spread + observation uncertainty error bars
│   ├── G_composite_iqr_mean_obs_spread/
│   ├── H_composite_climatology/
│   ├── I_all_experiments/           # all experiments × all sites per variable
│   ├── J_coverage_heatmap/          # site × variable CP heat map
│   ├── K_ss_heatmap/                # site × variable SS heat map
│   ├── L_seasonal_sigma_bars/       # seasonal ensemble sigma by experiment
│   ├── M_coverage_bars/             # average CP per experiment
│   ├── N_domain_heatmap/            # PFT-domain CP heat map
│   └── O_combined_coverage_domain/  # site and PFT coverage side by side
└── logs/
```

Figures are saved as both PDF (vector, for publication) and PNG (quick-look).

---

## Evaluation metrics

All metrics are computed for two temporal scopes: `all` (full observation
record) and `growing` (April–October).

| Metric  | Definition                                                                                                |
|---------|-----------------------------------------------------------------------------------------------------------|
| CP      | Coverage percentage — fraction of observations inside the 99 % ensemble envelope (min/max of 128 members) |
| MBE     | Mean bias error: mean(X̄ − O)                                                                              |
| RMSE    | Root mean square error                                                                                    |
| ubRMSE  | Unbiased RMSE = √(RMSE² − MBE²)                                                                           |
| σ       | Mean per-timestep ensemble standard deviation, evaluated only at observed timesteps                       |
| SS      | Spread-skill ratio = σ / ubRMSE                                                                           |

---

## Extending the pipeline

**Add a site** — append to `config.SITES`, `config.SITE_FULL`, and
`config.SITE_PFT`. If the site has a non-standard soil-layer layout, add an
entry to `config.LEVSOI_MAP`.

**Add a variable** — extend `config.VARIABLES` with the CLM5 variable name,
observation column name, label, unit, and scale factor. If the variable
requires a new NetCDF field, add it to `extract._NC_VARS` and handle it in
`extract._member_to_dataframe`.

**Change the ensemble envelope** — edit the `envelope` argument in
`summaries.ensemble_summary`. Switching to `"quantile"` uses
`config.COVERAGE_PERCENTILES` (default: 0.5th/99.5th percentile) instead of
min/max.

**Add a per-site figure family** — add a function to `plotting.py`, register
it in `config.FIGURE_FAMILIES`, and call it from `plotting.plot_all_families`.

**Add a composite figure** — add a function to `composite.py`, register it in
`config.COMPOSITE_FAMILIES`, add routing logic to
`config.composite_figure_path`, and call it from
`composite.render_all_composites`.

---
