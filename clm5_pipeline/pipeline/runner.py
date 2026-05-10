"""Orchestrator for the CLM5 ensemble evaluation pipeline.

Each (experiment, site) job walks through four stages:

    extract  → summarise → metrics → plot

Stages are idempotent and use cached CSVs so a subsequent run can skip any
stage that has already completed.  The runner is invoked both by the local CLI
(`run_pipeline.py`) and by the SLURM array scripts on JSC.
"""
from __future__ import annotations

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from ..config import (
    ALL_VARIABLES,
    CLIMATOLOGY_VARIABLES,
    ENSEMBLE_ENVELOPE,
    ENVELOPE_LOWER_Q,
    ENVELOPE_UPPER_Q,
    EXPERIMENTS,
    GROWING_MONTHS,
    OBS_UNAVAILABLE_SITES,
    OBS_VARIABLES,
    OUTPUT_DIRS,
    SITES,
    ensure_output_dirs,
    intermediate_path,
    metric_path,
    plot_input_path,
)
from . import climatology, composite, extract, io, metrics, observations, plotting, summaries

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Per-site work
# ---------------------------------------------------------------------------
def _summarise_variable(
    experiment: str,
    site: str,
    variable: str,
    force: bool = False,
):
    """Produce summary + merged + climatology CSVs for one variable.

    Returns a tuple (members_df, merged_df, climatology_df) or None when the
    intermediate is missing.
    """
    inter_path = intermediate_path(experiment, site, variable)
    if not inter_path.exists():
        log.warning("Missing intermediate %s — run extract first", inter_path)
        return None

    members = io.read_wide_ensemble_csv(inter_path)

    summary = summaries.ensemble_summary(
        members,
        envelope=ENSEMBLE_ENVELOPE,
        lower_q=ENVELOPE_LOWER_Q,
        upper_q=ENVELOPE_UPPER_Q,
    )

    obs_series = observations.get_obs_series(site, variable)
    merged = summaries.merge_summary_with_obs(summary, obs_series)

    # For TLAI, supply a pre-computed obs climatology so the per-observation
    # LAI_StdDev is used as the uncertainty (RMS across months) rather than
    # the inter-year standard deviation of monthly means.
    if variable == "TLAI":
        obs_clim = observations.get_lai_monthly_climatology(site)
        clim = climatology.climatology_table(
            members,
            obs_series,
            obs_clim=obs_clim,
        )
    else:
        clim = climatology.climatology_table(members, obs_series)

    # Persist plot inputs.
    io.write_csv(summary, plot_input_path(experiment, site, variable, "summary"))
    io.write_csv(merged, plot_input_path(experiment, site, variable, "merged"))
    io.write_csv(clim, plot_input_path(experiment, site, variable, "climatology"))

    return members, merged, clim


def _compute_site_metrics(experiment: str, site: str) -> pd.DataFrame:
    """Compute all/growing metrics for one experiment/site."""
    rows = []

    for variable in OBS_VARIABLES:
        inter_path = intermediate_path(experiment, site, variable)
        if not inter_path.exists():
            continue

        if site in OBS_UNAVAILABLE_SITES.get(variable, set()):
            continue

        members = io.read_wide_ensemble_csv(inter_path)

        summary = summaries.ensemble_summary(
            members,
            envelope=ENSEMBLE_ENVELOPE,
            lower_q=ENVELOPE_LOWER_Q,
            upper_q=ENVELOPE_UPPER_Q,
        )

        obs = observations.get_obs_series(site, variable)
        if obs is None:
            continue

        all_period = metrics.compute_all(summary, members, obs)

        growing = metrics.compute_all(
            summary,
            members,
            obs,
            month_filter=GROWING_MONTHS,
        )

        rows.append({
            "experiment": experiment,
            "site": site,
            "variable": variable,
            **{f"all_{k}": v for k, v in all_period.items()},
            **{f"growing_{k}": v for k, v in growing.items()},
        })

    return pd.DataFrame(rows)


def run_site(
    experiment: str,
    site: str,
    variables: Iterable[str] | None = None,
    force_extract: bool = False,
    do_plots: bool = True,
) -> dict:
    """End-to-end work for one (experiment, site) pair."""
    ensure_output_dirs()
    variables = list(variables or ALL_VARIABLES)

    report: dict = {
        "experiment": experiment,
        "site": site,
        "plots": {},
        "missing": [],
    }

    # 1. Extract.
    extracted = extract.extract_site(
        experiment,
        site,
        variables,
        force=force_extract,
    )
    report["extracted"] = {v: str(p) for v, p in extracted.items()}

    # 2. Summaries + plots per variable.
    for var in variables:
        result = _summarise_variable(experiment, site, var)

        if result is None:
            report["missing"].append(var)
            continue

        _members, merged, clim = result

        if do_plots:
            try:
                paths = plotting.plot_all_families(
                    merged,
                    clim,
                    experiment,
                    site,
                    var,
                )
                report["plots"][var] = {
                    k: [str(p) for p in v]
                    for k, v in paths.items()
                }
            except Exception as exc:  # pragma: no cover
                log.exception(
                    "Plotting failed for %s/%s/%s: %s",
                    experiment,
                    site,
                    var,
                    exc,
                )

    # 3. Metrics.
    metrics_df = _compute_site_metrics(experiment, site)

    if not metrics_df.empty:
        site_metric_file = (
            OUTPUT_DIRS["metrics"] / experiment / f"{site}_metrics.csv"
        )
        io.write_csv(metrics_df, site_metric_file)
        report["metrics"] = str(site_metric_file)

    return report


def _expected_metric_variables(
    site: str,
    variables: Iterable[str] | None = None,
) -> set[str]:
    """Metric variables expected for a site, respecting missing observations."""
    selected = set(variables or ALL_VARIABLES)
    expected = set(OBS_VARIABLES).intersection(selected)

    return {
        var for var in expected
        if site not in OBS_UNAVAILABLE_SITES.get(var, set())
    }


def _site_metric_file(experiment: str, site: str) -> Path:
    return OUTPUT_DIRS["metrics"] / experiment / f"{site}_metrics.csv"


def site_outputs_complete(
    experiment: str,
    site: str,
    variables: Iterable[str] | None = None,
    require_plot_inputs: bool = True,
) -> bool:
    """Return True when cached outputs for one experiment/site are complete."""
    selected = list(variables or ALL_VARIABLES)

    if require_plot_inputs:
        for variable in selected:
            if not plot_input_path(experiment, site, variable, "merged").exists():
                log.info(
                    "Incomplete %s/%s: missing merged plot input for %s",
                    experiment,
                    site,
                    variable,
                )
                return False

            if not plot_input_path(experiment, site, variable, "climatology").exists():
                log.info(
                    "Incomplete %s/%s: missing climatology plot input for %s",
                    experiment,
                    site,
                    variable,
                )
                return False

    metric_file = _site_metric_file(experiment, site)
    expected_metrics = _expected_metric_variables(site, selected)

    if expected_metrics:
        if not metric_file.exists():
            log.info(
                "Incomplete %s/%s: missing site metric file %s",
                experiment,
                site,
                metric_file,
            )
            return False

        try:
            df = pd.read_csv(metric_file)
        except Exception as exc:
            log.info(
                "Incomplete %s/%s: unreadable site metric file %s: %s",
                experiment,
                site,
                metric_file,
                exc,
            )
            return False

        if "variable" not in df.columns:
            log.info(
                "Incomplete %s/%s: metric file has no variable column",
                experiment,
                site,
            )
            return False

        have = set(df["variable"].dropna().astype(str))
        missing = expected_metrics - have

        if missing:
            log.info(
                "Incomplete %s/%s: metric file missing variables %s",
                experiment,
                site,
                sorted(missing),
            )
            return False

    return True


def find_incomplete_site_jobs(
    experiments: Iterable[str] = EXPERIMENTS,
    sites: Iterable[str] = SITES,
    variables: Iterable[str] | None = None,
    require_plot_inputs: bool = True,
) -> list[tuple[str, str]]:
    """List experiment/site pairs whose cached CSV outputs are incomplete."""
    jobs: list[tuple[str, str]] = []

    for experiment in experiments:
        for site in sites:
            if not site_outputs_complete(
                experiment,
                site,
                variables,
                require_plot_inputs=require_plot_inputs,
            ):
                jobs.append((experiment, site))

    return jobs


def repair_incomplete_site_jobs(
    experiments: Iterable[str] = EXPERIMENTS,
    sites: Iterable[str] = SITES,
    variables: Iterable[str] | None = None,
    workers: int = 1,
    force_extract: bool = False,
    do_plots: bool = True,
    require_plot_inputs: bool = True,
) -> list[dict]:
    """Rerun only experiment/site jobs with missing downstream CSV outputs."""
    jobs = find_incomplete_site_jobs(
        experiments,
        sites,
        variables,
        require_plot_inputs=require_plot_inputs,
    )

    if not jobs:
        log.info("No incomplete site jobs detected")
        return []

    log.warning("Repairing %d incomplete site jobs: %s", len(jobs), jobs)

    reports: list[dict] = []

    if workers > 1:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    run_site,
                    experiment,
                    site,
                    variables,
                    force_extract,
                    do_plots,
                ): (experiment, site)
                for experiment, site in jobs
            }

            for fut in as_completed(futures):
                reports.append(fut.result())
    else:
        for experiment, site in jobs:
            reports.append(
                run_site(
                    experiment,
                    site,
                    variables,
                    force_extract=force_extract,
                    do_plots=do_plots,
                )
            )

    reports.sort(key=lambda r: (r["experiment"], r["site"]))
    return reports


# ---------------------------------------------------------------------------
# Experiment-level helpers
# ---------------------------------------------------------------------------
def aggregate_experiment_metrics(experiment: str) -> list[Path]:
    """Stitch per-site metric CSVs into per (variable, scope) tables."""
    per_site_dir = OUTPUT_DIRS["metrics"] / experiment

    if not per_site_dir.exists():
        return []

    dfs = []

    for path in sorted(per_site_dir.glob("*_metrics.csv")):
        try:
            dfs.append(pd.read_csv(path))
        except Exception as exc:
            log.warning("Skipping unreadable metric file %s: %s", path, exc)

    if not dfs:
        log.warning(
            "No per-site metric CSVs found for experiment %s in %s",
            experiment,
            per_site_dir,
        )
        return []

    full = pd.concat(dfs, ignore_index=True)

    written: list[Path] = []

    for variable in OBS_VARIABLES:
        sub = full[full["variable"] == variable]

        if sub.empty:
            continue

        for scope in ("all", "growing"):
            scope_cols = [c for c in sub.columns if c.startswith(f"{scope}_")]

            tab = sub[["experiment", "site", "variable"] + scope_cols].copy()
            tab.columns = [c.replace(f"{scope}_", "") for c in tab.columns]

            path = metric_path(experiment, variable, scope)
            io.write_csv(tab, path)
            written.append(path)

    return written


def render_composites(
    experiments: Iterable[str] = EXPERIMENTS,
    variables: Iterable[str] | None = None,
) -> dict:
    """Render the multi-site / cross-experiment composite figures.

    Must run after site-level plot_inputs and metrics CSVs exist. Safe to
    re-run; each call overwrites existing PDFs/PNGs.
    """
    ensure_output_dirs()
    variables = list(variables or ALL_VARIABLES)

    return composite.render_all_composites(
        experiments=list(experiments),
        variables=variables,
    )


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------
def run_experiment(
    experiment: str,
    sites: Iterable[str] = SITES,
    variables: Iterable[str] | None = None,
    workers: int = 1,
    force_extract: bool = False,
    do_plots: bool = True,
) -> list[dict]:
    """Run the pipeline for every site in one experiment."""
    sites = list(sites)

    if workers > 1:
        reports: list[dict] = []

        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    run_site,
                    experiment,
                    site,
                    variables,
                    force_extract,
                    do_plots,
                ): site
                for site in sites
            }

            for fut in as_completed(futures):
                reports.append(fut.result())

        reports.sort(key=lambda r: r["site"])
    else:
        reports = [
            run_site(
                experiment,
                site,
                variables,
                force_extract,
                do_plots,
            )
            for site in sites
        ]

    aggregate_experiment_metrics(experiment)
    return reports


def run_all(
    experiments: Iterable[str] = EXPERIMENTS,
    sites: Iterable[str] = SITES,
    variables: Iterable[str] | None = None,
    workers: int = 1,
    force_extract: bool = False,
    do_plots: bool = True,
) -> dict[str, list[dict]]:
    """Run the pipeline for all requested experiments."""
    out: dict[str, list[dict]] = {}

    for exp in experiments:
        out[exp] = run_experiment(
            exp,
            sites,
            variables,
            workers,
            force_extract,
            do_plots,
        )

    return out