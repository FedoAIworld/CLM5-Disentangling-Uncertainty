#!/usr/bin/env python3
"""Command-line entry point for the CLM5 evaluation pipeline.

Typical JSC usage::

    # One experiment x one site (used by SLURM array)
    python run_pipeline.py --experiment forcing --site FI-Hyy

    # Whole experiment with parallel workers
    python run_pipeline.py --experiment combined --workers 14

    # Everything in BGC mode (default — 4 experiments, 14 sites)
    python run_pipeline.py --all

    # Everything in SP mode (1 experiment, 9 sites)
    python run_pipeline.py --mode sp --all

Pipeline modes
--------------
bgc (default)
    Full four-experiment evaluation over all 14 ICOS sites.
    EXPERIMENTS = [forcing, soil, vegetation, combined]
    SITES       = all 14 sites

sp
    Standard-physics combined-only evaluation over a 9-site subset.
    EXPERIMENTS = [combined]
    SITES       = FI-Hyy, SE-Svb, CZ-BK1, DE-RuW, NL-Loo,
                  FR-Pue, DE-Hai, DE-HoH, BE-Bra

The mode must be known before ``clm5_pipeline.config`` is imported (so that
``EXPERIMENTS`` and ``SITES`` are already set when argparse ``choices=`` is
evaluated).  We therefore scan ``sys.argv`` for ``--mode`` before any
pipeline import.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Early mode detection — must happen before any pipeline import so that
# clm5_pipeline.config reads the correct CLM5_PIPELINE_MODE value.
# ---------------------------------------------------------------------------
def _detect_mode_early() -> str:
    """Return the pipeline mode from sys.argv without argparse."""
    for i, arg in enumerate(sys.argv[1:], 1):
        if arg in ("--mode", "-mode"):
            # i is the 1-based index of arg in sys.argv; the value follows at i+1.
            if i + 1 < len(sys.argv):
                return sys.argv[i + 1].lower()
        if arg.startswith("--mode="):
            return arg.split("=", 1)[1].lower()
    return os.environ.get("CLM5_PIPELINE_MODE", "bgc").lower()


_mode = _detect_mode_early()
if _mode not in ("bgc", "sp"):
    sys.exit(f"error: --mode must be 'bgc' or 'sp', got {_mode!r}")
os.environ["CLM5_PIPELINE_MODE"] = _mode

# Make ``pipeline`` importable when running from inside the repo.
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from clm5_pipeline.config import (  # noqa: E402
    ALL_VARIABLES, EXPERIMENTS, SITES, OUTPUT_DIRS, PIPELINE_MODE,
    ensure_output_dirs,
)
from clm5_pipeline.pipeline import runner  # noqa: E402


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="CLM5 ensemble evaluation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--mode", choices=["bgc", "sp"], default=PIPELINE_MODE,
                   help=(
                       "Pipeline mode (default: %(default)s). "
                       "'bgc': 4 experiments × 14 sites. "
                       "'sp': combined only × 9 sites. "
                       "Can also be set via CLM5_PIPELINE_MODE env var."
                   ))
    p.add_argument("--experiment", choices=EXPERIMENTS,
                   help="Run only this experiment (default: all for current mode).")
    p.add_argument("--site", choices=SITES,
                   help="Run only this site (default: all sites for current mode).")
    p.add_argument("--variables", nargs="+", choices=ALL_VARIABLES,
                   help="Subset of variables to process. Default: all.")
    p.add_argument("--workers", type=int, default=1,
                   help="Parallel workers per experiment (sites run in parallel).")
    p.add_argument("--force", action="store_true",
                   help="Re-extract from NetCDF even if CSVs already exist.")
    p.add_argument("--no-plots", action="store_true",
                   help="Skip plot generation (useful for extract-only passes).")
    p.add_argument("--all", action="store_true",
                   help="Shortcut for: every experiment x every site.")
    p.add_argument("--log-level", default="INFO",
                   choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    p.add_argument("--composites-only", action="store_true",
                   help="Skip extract/summary/metrics and just render the "
                        "multi-site composite figures from cached CSVs.")
    p.add_argument("--with-composites", action="store_true",
                   help="Also render multi-site composite figures at the end "
                        "(only meaningful after per-site work is done).")
    p.add_argument("--repair-missing", action="store_true",
                   help="Before aggregation/composites, rerun experiment-site jobs "
                        "whose metric or plot-input CSVs are missing/incomplete.")
    p.add_argument("--aggregate-only", action="store_true",
                   help="Skip normal site processing; optionally repair missing "
                        "site jobs, aggregate metrics, and render composites.")
    return p.parse_args()


def _configure_logging(level: str) -> None:
    ensure_output_dirs()
    log_file = OUTPUT_DIRS["logs"] / f"pipeline_{time.strftime('%Y%m%d_%H%M%S')}.log"
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file),
    ]
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        handlers=handlers,
    )
    logging.info("Log file: %s", log_file)


def main() -> int:
    args = _parse_args()
    _configure_logging(args.log_level)
    log = logging.getLogger("run_pipeline")

    log.info(
        "Pipeline mode : %s | experiments: %s | sites (%d): %s",
        PIPELINE_MODE.upper(), EXPERIMENTS, len(SITES), SITES,
    )

    do_plots = not args.no_plots

    # Aggregate/composite path: useful as a dependent SLURM job after arrays.
    if args.composites_only or args.aggregate_only:
        experiments = [args.experiment] if args.experiment else EXPERIMENTS
        sites = [args.site] if args.site else SITES
        if args.repair_missing:
            log.info("Checking for missing/incomplete site outputs before aggregation")
            runner.repair_incomplete_site_jobs(
                experiments=experiments,
                sites=sites,
                variables=args.variables,
                workers=args.workers,
                force_extract=args.force,
                do_plots=do_plots,
            )
        for exp in experiments:
            written = runner.aggregate_experiment_metrics(exp)
            log.info("Aggregated %d metric tables for %s", len(written), exp)
        log.info("Rendering composite figures from cached plot_inputs / metrics")
        runner.render_composites(experiments=experiments, variables=args.variables)
        return 0

    if args.all or (args.experiment is None and args.site is None):
        log.info("Running ALL experiments x all sites")
        runner.run_all(
            experiments=EXPERIMENTS,
            sites=SITES,
            variables=args.variables,
            workers=args.workers,
            force_extract=args.force,
            do_plots=do_plots,
        )
        if args.with_composites:
            if args.repair_missing:
                log.info("Checking for missing/incomplete site outputs before composites")
                runner.repair_incomplete_site_jobs(
                    experiments=EXPERIMENTS,
                    sites=SITES,
                    variables=args.variables,
                    workers=args.workers,
                    force_extract=args.force,
                    do_plots=do_plots,
                )
            for exp in EXPERIMENTS:
                runner.aggregate_experiment_metrics(exp)
            log.info("Rendering composite figures")
            runner.render_composites(variables=args.variables)
        return 0

    experiments = [args.experiment] if args.experiment else EXPERIMENTS
    sites = [args.site] if args.site else SITES

    if args.site and args.experiment:
        log.info("Running single site %s / experiment %s", args.site, args.experiment)
        runner.run_site(
            args.experiment, args.site,
            variables=args.variables,
            force_extract=args.force,
            do_plots=do_plots,
        )
        return 0

    for exp in experiments:
        log.info("Running experiment %s across %d sites", exp, len(sites))
        runner.run_experiment(
            exp, sites,
            variables=args.variables,
            workers=args.workers,
            force_extract=args.force,
            do_plots=do_plots,
        )
    if args.with_composites:
        if args.repair_missing:
            log.info("Checking for missing/incomplete site outputs before composites")
            runner.repair_incomplete_site_jobs(
                experiments=experiments,
                sites=sites,
                variables=args.variables,
                workers=args.workers,
                force_extract=args.force,
                do_plots=do_plots,
            )
        for exp in experiments:
            runner.aggregate_experiment_metrics(exp)
        log.info("Rendering composite figures")
        runner.render_composites(experiments=experiments,
                                 variables=args.variables)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
