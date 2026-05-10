"""Multi-site composite figures for the CLM5 ensemble evaluation pipeline.

Ten figure families (E–O) are produced, each covering multiple sites and/or
experiments in a single layout:

    E  Per-experiment grid — ensemble spread vs observation with CP/SS annotations.
    F  Spread + observation + observation-uncertainty error bars (ET, H, NEE only).
    G  IQR band + ensemble mean + 99 % spread + observation per site.
    H  Monthly climatology grid per site.
    I  All four experiments × all sites in one grid per variable.
    J  Coverage-percentage heat map (site × variable).
    K  Spread-skill-ratio heat map (site × variable).
    L  Seasonal average ensemble sigma bar chart across experiments.
    M  Average coverage percentage per experiment (bar chart, two period scopes).
    N  PFT-domain heat map of average coverage percentage.
    O  Site-level and PFT-domain coverage heat maps side by side.

Every figure is saved as both PDF and PNG under ``figures/<COMPOSITE_FAMILY>/``.
Inputs are the ``plot_inputs/`` and ``metrics/`` CSVs written by the per-site
runs, so composite rendering requires no NetCDF reads.
"""
from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Iterable, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch

from ..config import (
    ALL_VARIABLES,
    CLIMATOLOGY_VARIABLES,
    EXPERIMENT_COLORS,
    EXPERIMENTS,
    EXPERIMENT_LABEL,
    OBS_UNAVAILABLE_SITES,
    OBS_VARIABLES,
    OUTPUT_DIRS,
    PLOT_STYLE,
    SEASON_MONTHS,
    SEASON_ORDER,
    SITES,
    SITE_FULL_NAME,
    SITE_PFT,
    VARIABLES,
    YLIMITS,
    composite_figure_path,
    plot_input_path,
)
from . import observations

log = logging.getLogger(__name__)

SPREAD_COLOR  = "#c6dbef"    #"#f03b20"
IQR_COLOR     = "#4292c6"    #"#feb24c"
MEAN_COLOR    = "#084594"    #"#2b8cbe"
OBS_COLOR     = "black"
OBS_UNC_COLOR = "#1f77b4"
Z_99          = 2.576        # 1-sigma -> 99% CI

# Month initials for climatology x-axis (JFMAMJJASOND).
MONTH_INITIALS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]

VARIABLE_DISPLAY_NAME = {
    "SM":  "Surface Soil Moisture",
    "SMR": "Root Zone Soil Moisture",
    "ET":  "Evapotranspiration",
    "H":   "Sensible Heat Flux",
    "NEE": "Net Ecosystem Exchange",
    "GPP": "Gross Primary Production",
}

_SIGMA_STYLE: dict = {
    "font.size": 18,
    "axes.linewidth": 2.5,
    "grid.linewidth": 1.5,
    "xtick.major.width": 2.0,
    "ytick.major.width": 2.0,
    "xtick.major.size": 8,
    "ytick.major.size": 8,
}

_PUB_STYLE: dict = {
    "font.size": 50,
    "font.family": "sans-serif",
    "axes.linewidth": 2.5,
    "grid.linewidth": 1.5,
    "xtick.major.width": 2.0,
    "ytick.major.width": 2.0,
    "xtick.major.size": 8,
    "ytick.major.size": 8,
}

_ALL_EXP_STYLE: dict = {
    "font.size": 20,
    "axes.linewidth": 2.5,
    "grid.linewidth": 1.5,
    "xtick.major.width": 2.0,
    "ytick.major.width": 2.0,
    "xtick.major.size": 8,
    "ytick.major.size": 8,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _apply_style() -> None:
    plt.rcParams.update(PLOT_STYLE)


def _panel_label(index: int) -> str:
    """Return a lowercase letter label: 'a', 'b', ..., 'z', 'aa', ..."""
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    if index < len(alphabet):
        return alphabet[index]
    return _panel_label(index // len(alphabet) - 1) + alphabet[index % len(alphabet)]


def _ylabel(variable: str) -> str:
    v = VARIABLES[variable]
    return f"{v['label']}{v['unit']}"


def _read_merged(experiment: str, site: str, variable: str) -> Optional[pd.DataFrame]:
    path = plot_input_path(experiment, site, variable, "merged")
    if not path.exists():
        return None
    return pd.read_csv(path, parse_dates=["datetime"])


def _read_climatology(experiment: str, site: str, variable: str) -> Optional[pd.DataFrame]:
    path = plot_input_path(experiment, site, variable, "climatology")
    if not path.exists():
        return None
    return pd.read_csv(path)


def _obs_xrange(merged: pd.DataFrame, pad_months: int = 1) -> Optional[tuple]:
    if "obs" not in merged.columns or merged["obs"].dropna().empty:
        return None
    mask = merged["obs"].notna()
    first = merged.loc[mask, "datetime"].min() - pd.DateOffset(months=pad_months)
    last = merged.loc[mask, "datetime"].max() + pd.DateOffset(months=pad_months)
    return first, last


def _read_site_metrics(experiment: str, scope: str = "all") -> pd.DataFrame:
    """Concat per-variable aggregated metrics CSVs into one site×variable frame."""
    frames = []
    for var in OBS_VARIABLES:
        path = OUTPUT_DIRS["metrics"] / experiment / f"metrics_{var}_{scope}.csv"
        if not path.exists():
            continue
        try:
            df = pd.read_csv(path)
            if "Site" in df.columns and "site" not in df.columns:
                df = df.rename(columns={"Site": "site"})
            df["variable"] = var
            frames.append(df)
        except Exception as exc:  # pragma: no cover
            log.warning("Could not read %s: %s", path, exc)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _site_metric(metrics_df: pd.DataFrame, site: str, variable: str) -> dict:
    """Return metrics dict for a (site, variable) pair."""
    if metrics_df.empty or "site" not in metrics_df.columns:
        return {}
    sub = metrics_df[(metrics_df["site"] == site) & (metrics_df["variable"] == variable)]
    if sub.empty:
        return {}
    return sub.iloc[0].to_dict()


def _save(fig: plt.Figure, path_fn) -> list[Path]:
    out = []
    for ext in ("pdf", "png"):
        p = path_fn(ext)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, bbox_inches="tight")
        out.append(p)
    plt.close(fig)
    return out


def _grid_dims(n: int, ncols: int = 3) -> tuple[int, int]:
    return math.ceil(n / ncols), ncols


# ---------------------------------------------------------------------------
# E — spread vs obs, one grid per (experiment, variable)
# ---------------------------------------------------------------------------
def plot_composite_spread_vs_obs(
    experiment: str,
    variable: str,
    sites: Iterable[str] = SITES,
    scope: str = "all",
    ncols: int = 3,
) -> list[Path]:
    _apply_style()
    sites = [s for s in sites if s not in OBS_UNAVAILABLE_SITES.get(variable, set())]

    usable = []
    merged_cache = {}
    for site in sites:
        merged = _read_merged(experiment, site, variable)
        if merged is None:
            continue
        if "obs" not in merged.columns or merged["obs"].dropna().empty:
            continue
        usable.append(site)
        merged_cache[site] = merged
    if not usable:
        log.info("No composite spread-vs-obs panels for %s / %s", experiment, variable)
        return []

    metrics_df = _read_site_metrics(experiment, scope=scope)
    nrows, ncols = _grid_dims(len(usable), ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(7.0 * ncols, 3.8 * nrows), squeeze=False)
    ylim = YLIMITS.get(variable)

    for idx, site in enumerate(usable):
        ax = axes[idx // ncols][idx % ncols]
        merged = merged_cache[site]
        dt = merged["datetime"]
        ax.fill_between(dt, merged["lb"], merged["ub"], color=SPREAD_COLOR, alpha=1.0, label="Ens. Spread (99% CI)")
        obs_mask = merged["obs"].notna()
        ax.plot(dt[obs_mask], merged.loc[obs_mask, "obs"], "-", color=OBS_COLOR, linewidth=1.6, label="Observation")
        if ylim is not None:
            ax.set_ylim(ylim)
        xr = _obs_xrange(merged)
        if xr is not None:
            ax.set_xlim(xr)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        for tick in ax.get_xticklabels():
            tick.set_rotation(90)

        full_name = SITE_FULL_NAME.get(site, site)
        pft = SITE_PFT.get(site, "")
        ax.set_title(full_name, fontsize=13, loc="left", pad=14)
        ax.text(0.98, 1.04, pft, transform=ax.transAxes, ha="right", va="bottom", fontsize=11)
        ax.text(0.98, 0.96, f"({_panel_label(idx)})", transform=ax.transAxes, ha="right", va="top", fontsize=11)

        m = _site_metric(metrics_df, site, variable)
        if m:
            cp = m.get("CP")
            ss = m.get("SS")
            if cp is not None and not pd.isna(cp) and ss is not None and not pd.isna(ss):
                ax.text(
                    0.02,
                    0.96,
                    f"CP: {cp:.1f} %; SS: {ss:.1f}",
                    transform=ax.transAxes,
                    ha="left",
                    va="top",
                    fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.7, lw=0),
                )

        ax.set_ylabel(_ylabel(variable) if (idx % ncols) == 0 else "")
        ax.grid(True, alpha=0.45)

    for j in range(len(usable), nrows * ncols):
        fig.delaxes(axes[j // ncols][j % ncols])

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=2, fontsize=12, frameon=True, fancybox=True, shadow=True)
    fig.subplots_adjust(hspace=0.5, wspace=0.25, top=0.93, bottom=0.05)

    def _path(ext: str) -> Path:
        return composite_figure_path("composite_spread_vs_obs", variable, ext, experiment=experiment, scope=scope)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# F — spread vs obs with obs-uncertainty errorbars
# ---------------------------------------------------------------------------
def plot_composite_spread_obs_unc(
    experiment: str,
    variable: str,
    sites: Iterable[str] = SITES,
    ncols: int = 3,
) -> list[Path]:
    if variable not in {"ET", "H", "NEE"}:
        return []

    plt.rcParams.update(_PUB_STYLE)
    sites = [s for s in sites if s not in OBS_UNAVAILABLE_SITES.get(variable, set())]
    usable: list[str] = []
    merged_cache: dict[str, pd.DataFrame] = {}
    unc_cache: dict[str, Optional[pd.Series]] = {}

    for site in sites:
        merged = _read_merged(experiment, site, variable)
        if merged is None:
            continue
        if "obs" not in merged.columns or merged["obs"].dropna().empty:
            continue
        usable.append(site)
        merged_cache[site] = merged
        unc_cache[site] = observations.get_obs_uncertainty(site, variable)

    if not usable:
        return []

    nrows = math.ceil(len(usable) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(15 * ncols, 10 * nrows), dpi=300, squeeze=False)
    fig.subplots_adjust(hspace=0.5, wspace=0.25, bottom=0.05, top=0.93)
    ylim = YLIMITS.get(variable)

    for idx, site in enumerate(usable):
        ax = axes[idx // ncols][idx % ncols]
        merged = merged_cache[site]
        dt = merged["datetime"]

        ax.fill_between(dt, merged["lb"], merged["ub"], color=SPREAD_COLOR, alpha=1.0, label="Ens. Spread (99% CI)")

        unc = unc_cache[site]
        obs_mask = merged["obs"].notna()
        if unc is not None and not unc.empty:
            unc_df = unc.rename("unc").to_frame().reset_index()
            unc_df.columns = ["datetime", "unc"]
            joined = merged[["datetime", "obs", "lb", "ub"]].merge(unc_df, on="datetime", how="left")
            has_unc = joined["obs"].notna() & joined["unc"].notna()
            no_unc = joined["obs"].notna() & joined["unc"].isna()

            if has_unc.any():
                obs_err = joined.loc[has_unc, "unc"] * Z_99
                ax.errorbar(
                    joined.loc[has_unc, "datetime"],
                    joined.loc[has_unc, "obs"],
                    yerr=obs_err,
                    fmt="o",
                    markersize=14,
                    color=OBS_COLOR,
                    ecolor=OBS_UNC_COLOR,
                    elinewidth=8.0,
                    capsize=15,
                    capthick=8.0,
                    zorder=7,
                    label="Obs. Unc. (99% CI)",
                )

                obs_unc_mean = float(obs_err.mean())
                ens_spread_mean = float((joined.loc[has_unc, "ub"] - joined.loc[has_unc, "lb"]).mean())
                ratio = ens_spread_mean / (2.0 * obs_unc_mean)
                metrics_txt = f"Obs Unc(99%): {obs_unc_mean:.2f}\nEns Spread:   {ens_spread_mean:.2f}\nRatio:        {ratio:.1f}"
                ax.text(0.02, 0.98, metrics_txt, transform=ax.transAxes, fontsize=38, va="top", bbox=dict(facecolor="white", alpha=0.8))

            if no_unc.any():
                ax.plot(joined.loc[no_unc, "datetime"], joined.loc[no_unc, "obs"], "o", markersize=14, color=OBS_COLOR, zorder=7)
        else:
            ax.plot(dt[obs_mask], merged.loc[obs_mask, "obs"], "o", markersize=14, color=OBS_COLOR, zorder=7, label="Observation")

        if ylim is not None:
            ax.set_ylim(ylim)
        xr = _obs_xrange(merged)
        if xr is not None:
            ax.set_xlim(xr)

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=50, rotation=90)
        ax.tick_params(axis="y", labelsize=50)
        ax.grid(True, linewidth=1.5, alpha=0.7)

        full_name = SITE_FULL_NAME.get(site, site)
        pft = SITE_PFT.get(site, "")
        ax.set_title(full_name, fontsize=50, loc="left")
        ax.text(0.95, 0.95, f"({_panel_label(idx)})", transform=ax.transAxes, fontsize=50, va="top", ha="right")
        ax.text(0.95, 1.09, pft, transform=ax.transAxes, fontsize=50, va="top", ha="right")
        ax.set_ylabel(_ylabel(variable) if (idx % ncols) == 0 else "", fontsize=50)

    for j in range(len(usable), nrows * ncols):
        fig.delaxes(axes[j // ncols][j % ncols])

    best_h, best_l = [], []
    for r in range(nrows):
        for c in range(ncols):
            h, l = axes[r][c].get_legend_handles_labels()
            if len(h) > len(best_h):
                best_h, best_l = h, l
    fig.legend(best_h, best_l, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=3, fontsize=50, frameon=True, fancybox=True, shadow=True)

    def _path(ext: str) -> Path:
        return composite_figure_path("composite_spread_obs_unc", variable, ext, experiment=experiment)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# G — IQR + mean + spread + obs
# ---------------------------------------------------------------------------
def plot_composite_iqr_mean_obs_spread(
    experiment: str,
    variable: str,
    sites: Iterable[str] = SITES,
    scope: str = "all",
    ncols: int = 3,
) -> list[Path]:
    plt.rcParams.update(_PUB_STYLE)
    sites = [s for s in sites if s not in OBS_UNAVAILABLE_SITES.get(variable, set())]
    usable: list[str] = []
    merged_cache: dict[str, pd.DataFrame] = {}

    for site in sites:
        merged = _read_merged(experiment, site, variable)
        if merged is None:
            continue
        usable.append(site)
        merged_cache[site] = merged

    if not usable:
        return []

    metrics_df = _read_site_metrics(experiment, scope=scope)
    nrows = math.ceil(len(usable) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(15 * ncols, 10 * nrows), dpi=300, squeeze=False)

    # Fixed top band for the external legend, avoiding overlap with top panels.
    top_adj = 0.90
    fig.subplots_adjust(hspace=0.55, wspace=0.25, bottom=0.05, top=top_adj)
    ylim = YLIMITS.get(variable)

    for idx, site in enumerate(usable):
        ax = axes[idx // ncols][idx % ncols]
        merged = merged_cache[site]
        dt = merged["datetime"]

        ax.fill_between(dt, merged["lb"], merged["ub"], color=SPREAD_COLOR, alpha=1.0, label="Ens. Spread (99% CI)")
        if "q25" in merged.columns and "q75" in merged.columns:
            ax.fill_between(dt, merged["q25"], merged["q75"], color=IQR_COLOR, alpha=0.6, label="IQR")
        if "mean" in merged.columns:
            ax.plot(dt, merged["mean"], "-", color=MEAN_COLOR, linewidth=3.5, label="Ensemble mean")

        if "obs" in merged.columns and merged["obs"].notna().any():
            obs_mask = merged["obs"].notna()
            ax.plot(dt[obs_mask], merged.loc[obs_mask, "obs"], "o", color=OBS_COLOR, markersize=14, zorder=7, label="Observation")

        if ylim is not None:
            ax.set_ylim(ylim)
        xr = _obs_xrange(merged)
        if xr is not None:
            ax.set_xlim(xr)
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=50, rotation=90)
        ax.tick_params(axis="y", labelsize=50)
        ax.grid(True, linewidth=1.5, alpha=0.7)

        full_name = SITE_FULL_NAME.get(site, site)
        pft = SITE_PFT.get(site, "")
        ax.set_title(full_name, fontsize=50, loc="left")
        ax.text(0.95, 0.95, f"({_panel_label(idx)})", transform=ax.transAxes, fontsize=50, va="top", ha="right")
        ax.text(0.95, 1.09, pft, transform=ax.transAxes, fontsize=50, va="top", ha="right")
        ax.set_ylabel(_ylabel(variable) if (idx % ncols) == 0 else "", fontsize=50)

        m = _site_metric(metrics_df, site, variable)
        if m:
            cp = m.get("CP")
            ss = m.get("SS")
            if cp is not None and not pd.isna(cp) and ss is not None and not pd.isna(ss):
                ax.text(
                    0.02,
                    0.98,
                    f"CP: {cp:.1f} %\nSS: {ss:.1f}",
                    transform=ax.transAxes,
                    fontsize=38,
                    va="top",
                    ha="left",
                    bbox=dict(facecolor="white", alpha=0.8),
                )

    for j in range(len(usable), nrows * ncols):
        fig.delaxes(axes[j // ncols][j % ncols])

    best_h, best_l = [], []
    for r in range(nrows):
        for c in range(ncols):
            h, l = axes[r][c].get_legend_handles_labels()
            if len(h) > len(best_h):
                best_h, best_l = h, l
    fig.legend(best_h, best_l, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=4, fontsize=50, frameon=True, fancybox=True, shadow=True)

    def _path(ext: str) -> Path:
        return composite_figure_path("composite_iqr_mean_obs_spread", variable, ext, experiment=experiment)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# H — monthly climatology grid
# ---------------------------------------------------------------------------
def plot_composite_climatology(
    experiment: str,
    variable: str,
    sites: Iterable[str] = SITES,
    ncols: int = 3,
) -> list[Path]:
    plt.rcParams.update(_PUB_STYLE)
    sites = [s for s in sites if s not in OBS_UNAVAILABLE_SITES.get(variable, set())]
    usable: list[str] = []
    clim_cache: dict[str, pd.DataFrame] = {}

    for site in sites:
        clim = _read_climatology(experiment, site, variable)
        if clim is None or clim.empty:
            continue
        usable.append(site)
        clim_cache[site] = clim

    if not usable:
        return []

    nrows = math.ceil(len(usable) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(15 * ncols, 10 * nrows), dpi=300, squeeze=False)

    top_adj = 0.90
    fig.subplots_adjust(hspace=0.55, wspace=0.25, bottom=0.05, top=top_adj)
    ylim = YLIMITS.get(variable)
    month_xs = list(range(1, 13))

    for idx, site in enumerate(usable):
        ax = axes[idx // ncols][idx % ncols]
        clim = clim_cache[site]
        months = clim["month"].astype(int).values

        if "min" in clim.columns and "max" in clim.columns:
            ax.fill_between(months, clim["min"], clim["max"], color=SPREAD_COLOR, alpha=1.0, label="Ens. Spread (99% CI)")
        if "q25" in clim.columns and "q75" in clim.columns:
            ax.fill_between(months, clim["q25"], clim["q75"], color=IQR_COLOR, alpha=0.6, label="IQR")
        if "mean" in clim.columns:
            ax.plot(months, clim["mean"], "-o", color=MEAN_COLOR, linewidth=3.5, markersize=14, label="Ensemble mean")
        if "obs_mean" in clim.columns and clim["obs_mean"].notna().any():
            has_std = "obs_std" in clim.columns and clim["obs_std"].notna().any()
            yerr = clim["obs_std"].values if has_std else None
            ax.errorbar(months, clim["obs_mean"], yerr=yerr, fmt="s--", color=OBS_COLOR, markersize=14, linewidth=3.0, capsize=8, capthick=3.0, label="Observation")

        ax.set_xticks(month_xs)
        ax.set_xticklabels(MONTH_INITIALS, rotation=0)
        if ylim is not None:
            ax.set_ylim(ylim)

        ax.tick_params(axis="x", labelsize=50)
        ax.tick_params(axis="y", labelsize=50)
        ax.grid(True, linewidth=1.5, alpha=0.7)

        full_name = SITE_FULL_NAME.get(site, site)
        pft = SITE_PFT.get(site, "")
        ax.set_title(full_name, fontsize=50, loc="left")
        ax.text(0.95, 0.95, f"({_panel_label(idx)})", transform=ax.transAxes, fontsize=50, va="top", ha="right")
        ax.text(0.95, 1.09, pft, transform=ax.transAxes, fontsize=50, va="top", ha="right")
        ax.set_ylabel(_ylabel(variable) if (idx % ncols) == 0 else "", fontsize=50)

        if "obs_mean" in clim.columns and "mean" in clim.columns and clim["obs_mean"].notna().any():
            valid = clim.dropna(subset=["obs_mean", "mean"])
            n = len(valid)
            bias = float((valid["mean"] - valid["obs_mean"]).mean())
            rmse = float(np.sqrt(((valid["mean"] - valid["obs_mean"]) ** 2).mean()))
            r = float(valid["mean"].corr(valid["obs_mean"])) if n >= 2 else float("nan")
            txt = f"n={n}\nMBE={bias:+.2f}\nRMSE={rmse:.2f}\nR={r:.2f}"
            ax.text(0.02, 0.98, txt, transform=ax.transAxes, fontsize=38, va="top", ha="left", bbox=dict(facecolor="white", alpha=0.8))

    for j in range(len(usable), nrows * ncols):
        fig.delaxes(axes[j // ncols][j % ncols])

    best_h, best_l = [], []
    for r in range(nrows):
        for c in range(ncols):
            h, l = axes[r][c].get_legend_handles_labels()
            if len(h) > len(best_h):
                best_h, best_l = h, l
    fig.legend(best_h, best_l, loc="upper center", bbox_to_anchor=(0.5, 0.985), ncol=4, fontsize=50, frameon=True, fancybox=True, shadow=True)

    def _path(ext: str) -> Path:
        return composite_figure_path("composite_climatology", variable, ext, experiment=experiment)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# I — all experiments × all sites, per variable
# ---------------------------------------------------------------------------
_I_EXP_LABELS = ["Forcing", "Soil", "Vegetation", "Combined"]


def plot_all_experiments_grid(
    variable: str,
    experiments: Iterable[str] = EXPERIMENTS,
    sites: Iterable[str] = SITES,
) -> list[Path]:
    plt.rcParams.update(_ALL_EXP_STYLE)
    experiments = list(experiments)
    sites = [s for s in sites if s not in OBS_UNAVAILABLE_SITES.get(variable, set())]
    n_rows = len(sites)
    n_cols = len(experiments)
    if n_rows == 0 or n_cols == 0:
        return []

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(7.5 * n_cols, 3.0 * n_rows), sharey=True, dpi=300, squeeze=False)
    fig.subplots_adjust(hspace=0.8, wspace=0.2)

    ylim = YLIMITS.get(variable)
    exp_col_labels = [EXPERIMENT_LABEL.get(e, e.capitalize()) for e in experiments]
    _short = {
        "Perturbed atmospheric forcing": "Forcing",
        "Perturbed soil parameters": "Soil",
        "Perturbed vegetation parameters": "Vegetation",
        "Combined perturbation": "Combined",
    }

    plot_idx = 0
    for r, site in enumerate(sites):
        for c, exp in enumerate(experiments):
            ax = axes[r][c]
            merged = _read_merged(exp, site, variable)

            if merged is None:
                ax.set_facecolor("#f5f5f5")
                ax.set_xticks([])
                ax.set_yticks([])
                plot_idx += 1
                continue

            dt = merged["datetime"]
            ax.fill_between(dt, merged["lb"], merged["ub"], color=SPREAD_COLOR, alpha=1.0)

            if "obs" in merged.columns and merged["obs"].notna().any():
                obs_mask = merged["obs"].notna()
                ax.plot(dt[obs_mask], merged.loc[obs_mask, "obs"], linestyle="-", color=OBS_COLOR, linewidth=3.5)

            if ylim is not None:
                ax.set_ylim(ylim)
            xr = _obs_xrange(merged)
            if xr is not None:
                ax.set_xlim(xr)

            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax.tick_params(axis="x", labelsize=16, rotation=45)
            ax.tick_params(axis="y", labelsize=16)
            ax.grid(True, linewidth=1.5, alpha=0.7)

            long_lbl = exp_col_labels[c]
            short_lbl = _short.get(long_lbl, long_lbl)
            ax.set_title(f"{site} - {short_lbl}", fontsize=16, loc="left")
            ax.text(0.95, 0.95, f"({_panel_label(plot_idx)})", transform=ax.transAxes, fontsize=12, va="top", ha="right")

            if c == 0:
                axes[r][0].set_ylabel(_ylabel(variable), fontsize=16)

            plot_idx += 1

    def _path(ext: str) -> Path:
        return composite_figure_path("all_experiments_grid", variable, ext, experiment=None)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# J/K helpers — coverage and spread-skill heat maps
# ---------------------------------------------------------------------------
def _cp_category(val: float) -> int:
    if pd.isna(val):
        return 0
    if val >= 90:
        return 3
    if val >= 50:
        return 2
    return 1


def _ss_category(val: float) -> int:
    if pd.isna(val):
        return 0
    if 0.6 <= val <= 1.0:
        return 3
    if val > 1.0:
        return 2
    return 1


def _categorize_df(df: pd.DataFrame, fn) -> pd.DataFrame:
    """Version-safe element-wise categorisation (pandas >= 2.1 or older)."""
    _ver = tuple(int(x) for x in pd.__version__.split(".")[:2])
    if _ver >= (2, 1):
        return df.map(fn).astype(float)
    return df.applymap(fn).astype(float)  # type: ignore[attr-defined]


def _make_heatmap(
    df: pd.DataFrame,
    categorize_fn,
    cmap_colors: list,
    cbar_labels: list[str],
    show_annot: bool = True,
) -> plt.Figure:
    categorized = _categorize_df(df, categorize_fn)
    annot_data = df.round(1).astype(object)
    annot_data[df.isna()] = "No Data"
    cmap = sns.color_palette(cmap_colors)

    fig_w = max(10, 1.4 * len(df.columns) + 2)
    fig_h = max(5, 0.65 * len(df) + 2)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    sns.heatmap(categorized, cmap=cmap, vmin=0, vmax=3, linewidths=0.8, annot=annot_data if show_annot else False, fmt="", cbar=False, annot_kws={"color": "black", "fontsize": 10}, ax=ax)
    ax.xaxis.tick_top()
    ax.tick_params(axis="x", labelsize=11)
    ax.tick_params(axis="y", labelsize=11)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

    cbar = fig.colorbar(ax.collections[0], ax=ax, orientation="horizontal", fraction=0.04, pad=0.10, aspect=40)
    cbar.set_ticks([0.375, 1.125, 1.875, 2.625])
    cbar.set_ticklabels(cbar_labels, fontsize=10)

    fig.tight_layout()
    return fig


def _build_metric_matrix(experiment: str, metric: str, scope: str = "all") -> pd.DataFrame:
    """Return a site × variable DataFrame for `metric` at `scope`."""
    cols = ["SM", "SMR", "ET", "H", "NEE", "GPP"]
    out = pd.DataFrame(index=SITES, columns=cols, dtype=float)

    for var in cols:
        agg_path = OUTPUT_DIRS["metrics"] / experiment / f"metrics_{var}_{scope}.csv"
        if not agg_path.exists():
            log.warning("Missing aggregated metric CSV: %s", agg_path)
            continue
        try:
            df = pd.read_csv(agg_path)
        except Exception as exc:
            log.warning("Could not read %s: %s", agg_path, exc)
            continue

        if "Site" in df.columns and "site" not in df.columns:
            df = df.rename(columns={"Site": "site"})

        if "site" not in df.columns:
            log.warning("Missing site column in %s", agg_path)
            continue

        if metric not in df.columns:
            log.warning("Missing metric %s in %s", metric, agg_path)
            continue

        for _, row in df.iterrows():
            site = row.get("site")
            if site in out.index:
                out.at[site, var] = row[metric]

    return out


def plot_coverage_heatmap(experiment: str = "combined", scope: str = "all") -> list[Path]:
    _apply_style()
    mat = _build_metric_matrix(experiment, "CP", scope=scope)
    if not mat.notna().any().any():
        return []
    mat = mat.rename(columns={"SMR": "SMr"})
    cmap = [(0.9, 0.9, 0.9), (1.0, 0.4, 0.4), (1.0, 0.8, 0.4), (0.4, 0.8, 0.4)]
    fig = _make_heatmap(mat, _cp_category, cmap, ["No Data", "Poor (<50%)", "Moderate (50-89%)", "Good (≥90%)"])

    def _path(ext: str) -> Path:
        return composite_figure_path("coverage_heatmap", "", ext, experiment=experiment, scope=scope)

    return _save(fig, _path)


def plot_ss_heatmap(experiment: str = "combined", scope: str = "all") -> list[Path]:
    _apply_style()
    mat = _build_metric_matrix(experiment, "SS", scope=scope)
    if not mat.notna().any().any():
        return []
    mat = mat.rename(columns={"SMR": "SMr"})
    cmap = [(0.9, 0.9, 0.9), (1.0, 0.4, 0.4), (1.0, 0.8, 0.4), (0.4, 0.8, 0.4)]
    fig = _make_heatmap(mat, _ss_category, cmap, ["No Data", "Underdispersed (<0.6)", "Overdispersed (>1)", "Calibrated (0.6–1)"])

    def _path(ext: str) -> Path:
        return composite_figure_path("ss_heatmap", "", ext, experiment=experiment, scope=scope)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# L — Seasonal average sigma bar chart
# ---------------------------------------------------------------------------
def _assign_season(month: int) -> str:
    for name, months in SEASON_MONTHS.items():
        if month in months:
            return name
    return "Unknown"


def plot_seasonal_sigma_bars(
    experiments: Iterable[str] = EXPERIMENTS,
    variables: Iterable[str] = ("SM", "SMR", "ET", "H", "NEE", "GPP"),
    sites: Iterable[str] = SITES,
) -> list[Path]:
    plt.rcParams.update(_SIGMA_STYLE)
    exp_list = list(experiments)
    var_list = list(variables)
    sites = list(sites)

    data: dict = {}
    for var in var_list:
        data[var] = {}
        excl = OBS_UNAVAILABLE_SITES.get(var, set())

        for exp in exp_list:
            season_buckets: dict[str, list] = {s: [] for s in SEASON_ORDER}

            for site in sites:
                if site in excl:
                    continue

                merged = _read_merged(exp, site, var)
                if merged is None:
                    continue

                df = merged.copy()

                if "std" in df.columns:
                    df["_sigma"] = df["std"]
                elif "lb" in df.columns and "ub" in df.columns:
                    df["_sigma"] = (df["ub"] - df["lb"]) / (2.0 * Z_99)
                else:
                    continue

                # Convert SM / SMR from % to cm³ cm⁻³.
                if var in ("SM", "SMR"):
                    df["_sigma"] = df["_sigma"] / 100.0

                df["_season"] = df["datetime"].dt.month.apply(_assign_season)

                for season in SEASON_ORDER:
                    vals = df.loc[df["_season"] == season, "_sigma"].dropna()
                    if not vals.empty:
                        season_buckets[season].append(float(vals.mean()))

            data[var][exp] = {
                s: float(np.nanmean(v)) if v else float("nan")
                for s, v in season_buckets.items()
            }

    ncols = 2
    nrows = 3
    fig, axes = plt.subplots(
        nrows,
        ncols,
        figsize=(8.0 * ncols, 5.5 * nrows),
        squeeze=False,
    )

    x = np.arange(len(SEASON_ORDER))
    width = 0.2

    last_vi = len(var_list) - 1
    legend_ax = None

    for vi, var in enumerate(var_list):
        ax = axes[vi // ncols][vi % ncols]

        for ei, exp in enumerate(exp_list):
            vals = [data[var][exp].get(s, float("nan")) for s in SEASON_ORDER]
            color = EXPERIMENT_COLORS.get(exp, f"C{ei}")

            ax.bar(
                x + ei * width,
                vals,
                width,
                color=color,
                edgecolor="black",
                linewidth=2.0,
                alpha=0.8,
                label=EXPERIMENT_LABEL.get(exp, exp),
            )

        ax.set_xticks(x + width * 1.5)
        ax.set_xticklabels(SEASON_ORDER)

        if var in ("SM", "SMR"):
            ax.set_ylabel(r"Avg $\sigma$ (cm$^3$ cm$^{-3}$)")
        else:
            ax.set_ylabel(r"Avg $\sigma$" + VARIABLES[var]["unit"])

        var_title = VARIABLE_DISPLAY_NAME.get(var, var)
        ax.set_title(f"({_panel_label(vi)}) {var_title}", loc="left")

        ax.grid(True, alpha=0.40, axis="y")

        if vi == last_vi:
            legend_ax = ax
            ymin, ymax = ax.get_ylim()
            ax.set_ylim(ymin, ymax * 1.18)

    for j in range(len(var_list), nrows * ncols):
        fig.delaxes(axes[j // ncols][j % ncols])

    if legend_ax is not None:
        handles, labels = legend_ax.get_legend_handles_labels()
        legend_ax.legend(
            handles,
            labels,
            loc="upper left",
            bbox_to_anchor=(1.01, 0.995),
            ncol=1,
            fontsize=12,
            frameon=True,
            fancybox=True,
            shadow=True,
            borderpad=0.35,
            labelspacing=0.35,
            handlelength=1.4,
            handletextpad=0.45,
        )

    fig.subplots_adjust(
        hspace=0.30,
        wspace=0.35,
        top=0.96,
        bottom=0.05,
        right=0.90,
    )

    def _path(ext: str) -> Path:
        return composite_figure_path("seasonal_sigma_bars", "", ext)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# M — Average CP per experiment
# ---------------------------------------------------------------------------
_SHORT_EXP = {
    "Perturbed atmospheric forcing": "Forcing",
    "Perturbed soil parameters": "Soil",
    "Perturbed vegetation parameters": "Vegetation",
    "Combined perturbation": "Combined",
}


def plot_coverage_bars(
    experiments: Iterable[str] = EXPERIMENTS,
    variables: Iterable[str] = ("SM", "ET", "H", "NEE"),
    sites: Iterable[str] = SITES,
) -> list[Path]:
    _apply_style()
    exp_list = list(experiments)
    var_list = list(variables)
    sites = list(sites)
    scopes = ["all", "growing"]

    ncols = len(var_list)
    nrows = len(scopes)

    fig, axes = plt.subplots(nrows, ncols, figsize=(3.6 * ncols, 4.4 * nrows), sharey=True, squeeze=False)
    x_pos = np.arange(len(exp_list))

    for ri, scope in enumerate(scopes):
        for vi, var in enumerate(var_list):
            ax = axes[ri][vi]
            excl = OBS_UNAVAILABLE_SITES.get(var, set())
            usable_sites = [s for s in sites if s not in excl]

            avg_cp: list[float] = []
            colors: list = []
            for exp in exp_list:
                agg_path = OUTPUT_DIRS["metrics"] / exp / f"metrics_{var}_{scope}.csv"
                colors.append(EXPERIMENT_COLORS.get(exp, "gray"))
                if not agg_path.exists():
                    avg_cp.append(float("nan"))
                    continue
                try:
                    df = pd.read_csv(agg_path)
                except Exception:
                    avg_cp.append(float("nan"))
                    continue
                if "CP" not in df.columns:
                    avg_cp.append(float("nan"))
                    continue
                if "Site" in df.columns and "site" not in df.columns:
                    df = df.rename(columns={"Site": "site"})
                valid = df[df["site"].isin(usable_sites)] if "site" in df.columns else df
                vals = valid["CP"].dropna()
                avg_cp.append(float(vals.mean()) if not vals.empty else float("nan"))

            bars = ax.bar(x_pos, avg_cp, width=0.58, color=colors, edgecolor="black", linewidth=0.8, alpha=0.85)

            # Bold CP values on top of each bar, one decimal place.
            for bar, val in zip(bars, avg_cp):
                if pd.isna(val):
                    continue
                ax.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    bar.get_height() + 1.5,
                    f"{val:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=8.5,
                    fontweight="bold",
                )

            exp_short = [_SHORT_EXP.get(EXPERIMENT_LABEL.get(e, e), e) for e in exp_list]
            ax.set_xticks(x_pos)
            ax.set_xticklabels(exp_short, rotation=0, ha="center", fontsize=9)
            ax.set_ylim(0, 112)

            panel_idx = ri * ncols + vi
            if ri == 0:
                ax.set_title(f"({_panel_label(panel_idx)}) {var}", loc="left", fontsize=12)
            else:
                ax.set_title(f"({_panel_label(panel_idx)})", loc="left", fontsize=12)

            if vi == 0:
                ax.set_ylabel("Average Coverage Percentage (%)", fontsize=11)
            ax.grid(True, alpha=0.35, axis="y")

    fig.subplots_adjust(hspace=0.18, wspace=0.16, top=0.96, bottom=0.10, left=0.07, right=0.99)

    def _path(ext: str) -> Path:
        return composite_figure_path("coverage_bars", "", ext)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# N — Domain heatmap
# ---------------------------------------------------------------------------
def _pft_order() -> list[str]:
    return ["ENF", "EBF", "DBF", "CRO", "MF"]


def _build_pft_cp_matrix(cp_mat: pd.DataFrame) -> pd.DataFrame:
    pft_rows = _pft_order()
    pft_sites: dict[str, list[str]] = {p: [] for p in pft_rows}
    for site, pft in SITE_PFT.items():
        if pft in pft_sites:
            pft_sites[pft].append(site)

    pft_cp = pd.DataFrame(index=pft_rows, columns=cp_mat.columns, dtype=float)
    for pft in pft_rows:
        for col in cp_mat.columns:
            var_key = "SMR" if col == "SMr" else col
            excl = OBS_UNAVAILABLE_SITES.get(var_key, set())
            group = [s for s in pft_sites.get(pft, []) if s in cp_mat.index and s not in excl]
            if group:
                vals = cp_mat.loc[group, col].dropna()
                pft_cp.at[pft, col] = float(vals.mean()) if not vals.empty else float("nan")
            else:
                pft_cp.at[pft, col] = float("nan")
    return pft_cp


def plot_domain_heatmap(experiment: str = "combined", scope: str = "all") -> list[Path]:
    _apply_style()
    cp_mat = _build_metric_matrix(experiment, "CP", scope=scope)
    if not cp_mat.notna().any().any():
        log.info("No CP data for domain heatmap (%s, %s)", experiment, scope)
        return []
    cp_mat = cp_mat.rename(columns={"SMR": "SMr"})
    pft_cp = _build_pft_cp_matrix(cp_mat)

    cmap = [(0.9, 0.9, 0.9), (1.0, 0.4, 0.4), (1.0, 0.8, 0.4), (0.4, 0.8, 0.4)]
    fig = _make_heatmap(pft_cp, _cp_category, cmap, ["No Data", "Structural (<50%)", "Mixed (50–90%)", "Parametric (≥90%)"], show_annot=False)

    def _path(ext: str) -> Path:
        return composite_figure_path("domain_heatmap", "", ext, experiment=experiment, scope=scope)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# O — combined coverage + domain heatmap
# ---------------------------------------------------------------------------
def plot_combined_coverage_domain_heatmap(experiment: str = "combined", scope: str = "all") -> list[Path]:
    _apply_style()
    cmap_colors = [(0.9, 0.9, 0.9), (1.0, 0.4, 0.4), (1.0, 0.8, 0.4), (0.4, 0.8, 0.4)]

    cp_mat = _build_metric_matrix(experiment, "CP", scope=scope)
    if not cp_mat.notna().any().any():
        log.info("No CP data for combined heatmap (%s, %s)", experiment, scope)
        return []
    cp_mat = cp_mat.rename(columns={"SMR": "SMr"})
    pft_cp = _build_pft_cp_matrix(cp_mat)

    cat_cp = _categorize_df(cp_mat, _cp_category)
    cat_pft = _categorize_df(pft_cp, _cp_category)
    annot_cp = cp_mat.round(1).astype(object)
    annot_cp[cp_mat.isna()] = "No Data"

    cmap_sns = sns.color_palette(cmap_colors)

    n_sites = len(cp_mat)
    n_vars = len(cp_mat.columns)

    cell_w = 1.35
    cell_h = 0.55
    fig_w = max(16.5, 2 * (cell_w * n_vars + 1.2))
    main_h = max(8.0, cell_h * n_sites + 1.4)
    cbar_h = 0.42
    leg_h = 0.95
    spacer_h = 0.2

    fig = plt.figure(figsize=(fig_w, main_h + cbar_h + leg_h + spacer_h))
    gs = GridSpec(4, 2, figure=fig, height_ratios=[main_h, spacer_h, cbar_h, leg_h], hspace=0.015, wspace=0.18)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_cbar = fig.add_subplot(gs[2, 0])
    ax_leg = fig.add_subplot(gs[2, 1])

    sns.heatmap(cat_cp, cmap=cmap_sns, vmin=0, vmax=3, linewidths=0.8, annot=annot_cp, fmt="", cbar=False, annot_kws={"color": "black", "fontsize": 10}, ax=ax_a)
    ax_a.xaxis.tick_top()
    ax_a.tick_params(axis="x", labelsize=11, pad=6)
    ax_a.tick_params(axis="y", labelsize=11)
    ax_a.set_yticklabels(ax_a.get_yticklabels(), rotation=0)
    ax_a.text(-0.08, 1.02, "(a)", transform=ax_a.transAxes, ha="left", va="bottom", fontsize=12, fontweight="bold")

    cb = fig.colorbar(ax_a.collections[0], cax=ax_cbar, orientation="horizontal")
    cb.set_ticks([0.375, 1.125, 1.875, 2.625])
    cb.set_ticklabels(["No Data", "Poor (<50%)", "Moderate (50-89%)", "Good (≥90%)"], fontsize=10)
    cb.ax.tick_params(pad=3)

    sns.heatmap(cat_pft, cmap=cmap_sns, vmin=0, vmax=3, linewidths=0.8, annot=False, cbar=False, ax=ax_b)
    ax_b.xaxis.tick_top()
    ax_b.tick_params(axis="x", labelsize=11, pad=6)
    ax_b.tick_params(axis="y", labelsize=11)
    ax_b.set_yticklabels(ax_b.get_yticklabels(), rotation=0)
    ax_b.text(-0.08, 1.02, "(b)", transform=ax_b.transAxes, ha="left", va="bottom", fontsize=12, fontweight="bold")

    ax_leg.axis("off")
    domain_patches = [
        Patch(facecolor=(0.4, 0.8, 0.4), edgecolor="black", label="Parametric domain (CP ≥ 90 %)"),
        Patch(facecolor=(1.0, 0.8, 0.4), edgecolor="black", label="Mixed domain (50 % ≤ CP < 90 %)"),
        Patch(facecolor=(1.0, 0.4, 0.4), edgecolor="black", label="Structural domain (CP < 50 %)"),
        Patch(facecolor=(0.9, 0.9, 0.9), edgecolor="black", label="No data"),
    ]
    ax_leg.legend(
        handles=domain_patches,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.08),
        fontsize=11,
        frameon=True,
        ncol=1,
        handlelength=1.8,
        handleheight=1.0,
        borderpad=0.35,
        labelspacing=0.35,
    )

    def _path(ext: str) -> Path:
        return composite_figure_path("combined_coverage_domain", "", ext, experiment=experiment, scope=scope)

    return _save(fig, _path)


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------
def render_all_composites(
    experiments: Iterable[str] = EXPERIMENTS,
    variables: Iterable[str] = ALL_VARIABLES,
) -> dict:
    """Render every composite figure family from cached plot_inputs / metrics."""
    result: dict = {
        "composite_spread_vs_obs": {},
        "composite_spread_obs_unc": {},
        "composite_iqr_mean_obs_spread": {},
        "composite_climatology": {},
        "all_experiments_grid": {},
        "coverage_heatmap": {},
        "ss_heatmap": {},
        "seasonal_sigma_bars": [],
        "coverage_bars": [],
        "domain_heatmap": {},
        "combined_coverage_domain": {},
    }
    experiments = list(experiments)
    variables = list(variables)

    for exp in experiments:
        for var in variables:
            if var in OBS_VARIABLES:
                paths = plot_composite_spread_vs_obs(exp, var)
                if paths:
                    result["composite_spread_vs_obs"].setdefault(exp, {})[var] = [str(p) for p in paths]

                paths = plot_composite_iqr_mean_obs_spread(exp, var)
                if paths:
                    result["composite_iqr_mean_obs_spread"].setdefault(exp, {})[var] = [str(p) for p in paths]

            if var in CLIMATOLOGY_VARIABLES:
                paths = plot_composite_climatology(exp, var)
                if paths:
                    result["composite_climatology"].setdefault(exp, {})[var] = [str(p) for p in paths]

            if var in {"ET", "H", "NEE"}:
                paths = plot_composite_spread_obs_unc(exp, var)
                if paths:
                    result["composite_spread_obs_unc"].setdefault(exp, {})[var] = [str(p) for p in paths]

    for var in variables:
        paths = plot_all_experiments_grid(var, experiments=experiments)
        if paths:
            result["all_experiments_grid"][var] = [str(p) for p in paths]

    for exp in experiments:
        for scope in ("all", "growing"):
            cp_paths = plot_coverage_heatmap(experiment=exp, scope=scope)
            if cp_paths:
                result["coverage_heatmap"].setdefault(exp, {})[scope] = [str(p) for p in cp_paths]
            ss_paths = plot_ss_heatmap(experiment=exp, scope=scope)
            if ss_paths:
                result["ss_heatmap"].setdefault(exp, {})[scope] = [str(p) for p in ss_paths]

    paths = plot_seasonal_sigma_bars(experiments=experiments)
    if paths:
        result["seasonal_sigma_bars"] = [str(p) for p in paths]

    paths = plot_coverage_bars(experiments=experiments)
    if paths:
        result["coverage_bars"] = [str(p) for p in paths]

    for exp in experiments:
        for scope in ("all", "growing"):
            paths = plot_domain_heatmap(experiment=exp, scope=scope)
            if paths:
                result["domain_heatmap"].setdefault(exp, {})[scope] = [str(p) for p in paths]

    for exp in experiments:
        for scope in ("all", "growing"):
            paths = plot_combined_coverage_domain_heatmap(experiment=exp, scope=scope)
            if paths:
                result["combined_coverage_domain"].setdefault(exp, {})[scope] = [str(p) for p in paths]

    return result
