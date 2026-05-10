"""Figure families for the CLM5 ensemble evaluation pipeline.

All figures are rendered as both PDF and PNG. The caller supplies a *summary* dataframe (from
``summaries.merge_summary_with_obs``) and a *climatology* dataframe (from
``climatology.climatology_table``) which contain everything needed to draw.

Four families
-------------
A  spread_vs_obs         ensemble min/max + observation
B  iqr_mean_obs_spread   IQR band + ensemble mean + 99% spread + obs
C  obs_mean_only         observation vs ensemble mean only
D  climatology           monthly climatology (12 months on x-axis)
"""
from __future__ import annotations

import calendar
import logging
from pathlib import Path
from typing import Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config import (
    EXPERIMENT_LABEL,
    FIGURE_FAMILIES,
    PLOT_STYLE,
    SITE_FULL_NAME,
    SITE_PFT,
    VARIABLES,
    YLIMITS,
    figure_path,
)

log = logging.getLogger(__name__)

# Grayscale luminances: spread 0.94 | IQR 0.70 | mean 0.23 | obs 0.00
SPREAD_COLOR = "#c6dbef"   # light blue
IQR_COLOR    = "#4292c6"   # mid blue  
MEAN_COLOR   = "#084594"   # dark blue 
OBS_COLOR    = "black"


def _apply_style():
    plt.rcParams.update(PLOT_STYLE)


def _save(fig: plt.Figure, family: str, experiment: str, variable: str,
          site: str) -> list[Path]:
    out_paths = []
    for ext in ("pdf", "png"):
        p = figure_path(family, experiment, variable, site, ext)
        p.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(p, bbox_inches="tight")
        out_paths.append(p)
    plt.close(fig)
    return out_paths


def _title(site: str, variable: str, experiment: str) -> str:
    full = SITE_FULL_NAME.get(site, site)
    pft = SITE_PFT.get(site, "")
    return f"{full} ({pft}) — {EXPERIMENT_LABEL[experiment]}"


def _ylabel(variable: str) -> str:
    v = VARIABLES[variable]
    return f"{v['label']}{v['unit']}"


def _obs_xrange(merged: pd.DataFrame, pad_months: int = 1) -> Optional[tuple]:
    """Return (xmin, xmax) covering the obs window only.

    If no observation is present in ``merged``, return None (so the caller
    leaves the x-axis on the full model range).  The window is widened by
    ``pad_months`` on each side so the first/last obs point isn't clipped
    by the axis spine.
    """
    if "obs" not in merged.columns or merged["obs"].dropna().empty:
        return None
    mask = merged["obs"].notna()
    first = merged.loc[mask, "datetime"].min()
    last  = merged.loc[mask, "datetime"].max()
    # Pad by whole months so year-level ticks still line up.
    first = first - pd.DateOffset(months=pad_months)
    last  = last  + pd.DateOffset(months=pad_months)
    return first, last


def _apply_xrange(ax, merged: pd.DataFrame, variable: str) -> None:
    """Clip x-axis to the obs-covered window when obs exist.

    TLAI is left alone — for TLAI the family A/B/C plots draw the full model
    time series and the obs come as sparse ICOS measurements, so an obs-only
    window would be misleading.
    """
    if variable == "TLAI":
        return
    xr = _obs_xrange(merged)
    if xr is not None:
        ax.set_xlim(xr)


# ---------------------------------------------------------------------------
# Family A - ensemble spread vs observation
# ---------------------------------------------------------------------------
def plot_spread_vs_obs(merged: pd.DataFrame,
                       experiment: str,
                       site: str,
                       variable: str,
                       ylimits: Optional[tuple[float, float]] = None) -> list[Path]:
    _apply_style()
    fig, ax = plt.subplots(figsize=(12, 6))
    dt = merged["datetime"]
    ax.fill_between(dt, merged["lb"], merged["ub"],
                    color=SPREAD_COLOR, alpha=0.35,
                    label="Ensemble spread (99% CI)")
    if "obs" in merged and merged["obs"].notna().any():
        ax.plot(dt, merged["obs"], "o--", color=OBS_COLOR,
                markersize=4, linewidth=1.0, label="Observation")
    ax.set_ylabel(_ylabel(variable))
    ax.set_xlabel("Date")
    ax.set_title(_title(site, variable, experiment))
    if ylimits or variable in YLIMITS:
        ax.set_ylim(ylimits or YLIMITS[variable])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _apply_xrange(ax, merged, variable)
    ax.grid(True, alpha=0.5)
    ax.legend(loc="upper left")
    return _save(fig, "spread_vs_obs", experiment, variable, site)


# ---------------------------------------------------------------------------
# Family B - IQR + mean + spread + obs
# ---------------------------------------------------------------------------
def plot_iqr_mean_obs_spread(merged: pd.DataFrame,
                             experiment: str,
                             site: str,
                             variable: str,
                             ylimits: Optional[tuple[float, float]] = None) -> list[Path]:
    _apply_style()
    fig, ax = plt.subplots(figsize=(12, 6))
    dt = merged["datetime"]
    ax.fill_between(dt, merged["lb"], merged["ub"],
                    color=SPREAD_COLOR, alpha=0.25,
                    label="99% CI (min-max)")
    ax.fill_between(dt, merged["q25"], merged["q75"],
                    color=IQR_COLOR, alpha=0.55,
                    label="IQR (Q25-Q75)")
    ax.plot(dt, merged["mean"], "-", color=MEAN_COLOR, linewidth=1.8,
            label="Ensemble mean")
    if "obs" in merged and merged["obs"].notna().any():
        ax.plot(dt, merged["obs"], "o", color=OBS_COLOR, markersize=4,
                label="Observation")
    ax.set_ylabel(_ylabel(variable))
    ax.set_xlabel("Date")
    ax.set_title(_title(site, variable, experiment))
    if ylimits or variable in YLIMITS:
        ax.set_ylim(ylimits or YLIMITS[variable])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _apply_xrange(ax, merged, variable)
    ax.grid(True, alpha=0.5)
    ax.legend(loc="upper left")
    return _save(fig, "iqr_mean_obs_spread", experiment, variable, site)


# ---------------------------------------------------------------------------
# Family C - observation + ensemble mean only
# ---------------------------------------------------------------------------
def plot_obs_mean_only(merged: pd.DataFrame,
                       experiment: str,
                       site: str,
                       variable: str,
                       ylimits: Optional[tuple[float, float]] = None) -> list[Path]:
    _apply_style()
    fig, ax = plt.subplots(figsize=(12, 6))
    dt = merged["datetime"]
    ax.plot(dt, merged["mean"], "-", color=MEAN_COLOR, linewidth=1.8,
            label="Ensemble mean")
    if "obs" in merged and merged["obs"].notna().any():
        ax.plot(dt, merged["obs"], "o--", color=OBS_COLOR, markersize=4,
                linewidth=1.0, label="Observation")
    ax.set_ylabel(_ylabel(variable))
    ax.set_xlabel("Date")
    ax.set_title(_title(site, variable, experiment))
    if ylimits or variable in YLIMITS:
        ax.set_ylim(ylimits or YLIMITS[variable])
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    _apply_xrange(ax, merged, variable)
    ax.grid(True, alpha=0.5)
    ax.legend(loc="upper left")
    return _save(fig, "obs_mean_only", experiment, variable, site)


# ---------------------------------------------------------------------------
# Family D - climatology
# ---------------------------------------------------------------------------
def plot_climatology(clim: pd.DataFrame,
                     experiment: str,
                     site: str,
                     variable: str,
                     ylimits: Optional[tuple[float, float]] = None) -> list[Path]:
    _apply_style()
    fig, ax = plt.subplots(figsize=(10, 6))
    months = clim["month"].values
    labels = [calendar.month_abbr[int(m)] for m in months]

    if "min" in clim and "max" in clim:
        ax.fill_between(months, clim["min"], clim["max"],
                        color=SPREAD_COLOR, alpha=0.2,
                        label="Ensemble range")
    if "q25" in clim and "q75" in clim:
        ax.fill_between(months, clim["q25"], clim["q75"],
                        color=IQR_COLOR, alpha=0.55,
                        label="IQR")
    if "mean" in clim:
        ax.plot(months, clim["mean"], "-o", color=MEAN_COLOR, linewidth=2.0,
                markersize=5, label="Ensemble mean")
    if "obs_mean" in clim and clim["obs_mean"].notna().any():
        ax.errorbar(months, clim["obs_mean"], yerr=clim.get("obs_std"),
                    fmt="s--", color=OBS_COLOR, markersize=6, linewidth=1.0,
                    capsize=3, label="Observation")

    ax.set_xticks(range(1, 13))
    ax.set_xticklabels([calendar.month_abbr[i] for i in range(1, 13)])
    ax.set_xlabel("Month")
    ax.set_ylabel(_ylabel(variable))
    ax.set_title(f"Monthly climatology — {_title(site, variable, experiment)}")
    if ylimits or variable in YLIMITS:
        ax.set_ylim(ylimits or YLIMITS[variable])
    ax.grid(True, alpha=0.5)
    ax.legend(loc="best")
    return _save(fig, "climatology", experiment, variable, site)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------
def plot_all_families(merged: pd.DataFrame,
                      climatology_df: pd.DataFrame,
                      experiment: str,
                      site: str,
                      variable: str) -> dict[str, list[Path]]:
    """Render every family and return a dict {family: [paths]}."""
    results: dict[str, list[Path]] = {}
    # TLAI: model-only time series doesn't really have a meaningful obs line;
    # we skip families A/B/C when no obs is available for the site and instead
    # lean on the climatology plot.
    obs_present = "obs" in merged.columns and merged["obs"].notna().any()

    try:
        if obs_present or variable != "TLAI":
            results["spread_vs_obs"] = plot_spread_vs_obs(
                merged, experiment, site, variable)
            results["iqr_mean_obs_spread"] = plot_iqr_mean_obs_spread(
                merged, experiment, site, variable)
            results["obs_mean_only"] = plot_obs_mean_only(
                merged, experiment, site, variable)
    except Exception as exc:  # pragma: no cover - plotting safety net
        log.exception("Time-series plotting failed for %s/%s/%s: %s",
                      experiment, site, variable, exc)

    try:
        results["climatology"] = plot_climatology(
            climatology_df, experiment, site, variable)
    except Exception as exc:  # pragma: no cover
        log.exception("Climatology plotting failed for %s/%s/%s: %s",
                      experiment, site, variable, exc)

    return results
