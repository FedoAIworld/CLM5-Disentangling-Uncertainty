#!/usr/bin/env python3
"""Lightweight sanity checks for the CLM5 pipeline.

Run locally (or on the cluster login node) to verify:

  1. All modules import cleanly.
  2. Paths in ``config.py`` resolve sensibly.
  3. Observation loaders read the CSVs bundled in ``Datasets/obs_data``.
  4. Summary / metric math produces the expected answers on a tiny synthetic
     ensemble (CP, MBE, RMSE, ubRMSE, SS).
  5. The runner's extract step works against a synthetic NetCDF fixture.

It does NOT try to read 4 experiments × 14 sites × 128 NetCDFs — that is
what the SLURM array is for.  This script is safe to run repeatedly; every
output goes to ``./_verify_tmp`` in the current directory.
"""
from __future__ import annotations

import math
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # make clm5_pipeline importable

from clm5_pipeline import config  # noqa: E402
from clm5_pipeline.pipeline import (  # noqa: E402
    climatology, composite, extract, io, metrics, observations, plotting,
    summaries,
)


# ---------------------------------------------------------------------------
# 1 / 2  — module imports and config sanity
# ---------------------------------------------------------------------------
def check_imports() -> None:
    assert len(config.SITES) == 14, "Expected 14 sites"
    assert set(config.EXPERIMENTS) == {"forcing", "soil", "vegetation", "combined"}
    assert config.VARIABLES["ET"]["scale"] == 86400.0
    assert config.VARIABLES["NEE"]["scale"] == 86400.0, \
        "NEE must also be scaled to gC m-2 d-1"
    assert config.VARIABLES["GPP"]["scale"] == 86400.0, \
        "GPP must also be scaled to gC m-2 d-1"
    assert config.VARIABLES["SM"]["scale"] == 100.0
    assert config.VARIABLES["SMR"]["scale"] == 100.0
    assert config.VARIABLES["ET"]["label"] == "ET"
    assert config.VARIABLES["H"]["label"] == "H"
    assert config.VARIABLES["SM"]["label"] == "SM"
    assert config.VARIABLES["SMR"]["label"] == "SMR"
    assert config.YLIMITS["TLAI"] == (0, 10), \
        f"TLAI ylim expected (0,10), got {config.YLIMITS['TLAI']}"
    assert config.N_ENSEMBLE == 128
    print("[OK] imports & config constants (short labels, 86400 scales, TLAI ylim 0-10)")


def check_paths() -> None:
    # These should all be Path objects.
    for key, p in config.OUTPUT_DIRS.items():
        assert isinstance(p, Path), f"OUTPUT_DIRS[{key}] is not a Path"
    # Don't require existence on JSC.
    print(f"[OK] MODEL_BASE_DIR = {config.MODEL_BASE_DIR}")
    print(f"[OK] OUTPUT_ROOT    = {config.OUTPUT_ROOT}")
    print(f"[OK] OBS_DIR        = {config.OBS_DIR}")


# ---------------------------------------------------------------------------
# 3  — observation loaders against the workspace CSVs
# ---------------------------------------------------------------------------
def check_observations() -> None:
    if not config.OBS_FLUX_CSV.exists():
        print(f"[WARN] Obs CSV not present at {config.OBS_FLUX_CSV} — skipping")
        return
    fluxes = observations.load_flux_obs()
    assert not fluxes.empty, "Flux obs frame is empty"
    assert "FI-Hyy_ET" in fluxes.columns
    # Spot-check SM / SMR for ES-Cnd (should be absent).
    assert observations.get_obs_series("ES-Cnd", "SM") is None
    assert observations.get_obs_series("SE-Svb", "SMR") is None
    et = observations.get_obs_series("FI-Hyy", "ET")
    assert et is not None and len(et.dropna()) > 0
    print(f"[OK] observations loader — FI-Hyy ET has {et.dropna().size} points")


# ---------------------------------------------------------------------------
# 4  — math on a synthetic ensemble
# ---------------------------------------------------------------------------
def _synthetic_ensemble(n_time: int = 24, n_members: int = 128,
                        rng_seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(rng_seed)
    time = pd.date_range("2015-01-01", periods=n_time, freq="MS")
    obs = pd.Series(
        np.sin(np.arange(n_time) / 3.0) + 2.0,
        index=time, name="obs"
    )
    # Ensemble = obs + per-member noise + small systematic bias.
    noise = rng.normal(0, 0.3, size=(n_time, n_members))
    members = obs.values[:, None] + noise + 0.1  # +0.1 bias
    cols = {f"real_{i}": members[:, i] for i in range(n_members)}
    df = pd.DataFrame({"datetime": time, **cols})
    return df, obs


def check_summaries_and_metrics() -> None:
    members, obs = _synthetic_ensemble()
    summary = summaries.ensemble_summary(members)
    assert set(["mean", "median", "std", "min", "max", "q25", "q75", "iqr",
                "lb", "ub"]).issubset(summary.columns)
    assert np.allclose(summary["iqr"], summary["q75"] - summary["q25"])

    # CP — 99% of obs should fall within min/max of 128 members.
    merged = summary.copy()
    merged["obs"] = obs.values
    cp = metrics.coverage_percent(merged["obs"], merged["lb"], merged["ub"])
    assert 80.0 <= cp <= 100.0, f"CP out of range: {cp}"

    mbe = metrics.mbe(obs.values, summary["mean"])
    assert abs(mbe - 0.1) < 0.1, f"MBE wrong: {mbe}"

    rmse = metrics.rmse(obs.values, summary["mean"])
    ub = metrics.ubrmse(obs.values, summary["mean"])
    assert ub <= rmse + 1e-9, "ubRMSE must be <= RMSE"

    all_m = metrics.compute_all(summary, members, obs)
    assert math.isfinite(all_m["SS"])  # sigma/ubrmse well-defined
    print(f"[OK] metrics — CP={cp:.1f}%, MBE={mbe:+.3f}, RMSE={rmse:.3f}, "
          f"ubRMSE={ub:.3f}, SS={all_m['SS']:.2f}")

    # Climatology round-trip.
    clim = climatology.climatology_table(members, obs)
    assert len(clim) == 12
    assert {"mean", "q25", "q75", "min", "max"}.issubset(clim.columns)
    print(f"[OK] climatology — 12-month table with mean/IQR/range")


# ---------------------------------------------------------------------------
# 5  — plotting smoke test (PDF + PNG)
# ---------------------------------------------------------------------------
def check_plotting() -> None:
    tmp_out = HERE / "_verify_tmp"
    tmp_out.mkdir(exist_ok=True)
    original_root = config.OUTPUT_ROOT
    original_dirs = config.OUTPUT_DIRS.copy()
    try:
        # Redirect figure_path to tmp for this test.
        config.OUTPUT_ROOT = tmp_out
        for k in config.OUTPUT_DIRS:
            config.OUTPUT_DIRS[k] = tmp_out / k
            config.OUTPUT_DIRS[k].mkdir(parents=True, exist_ok=True)

        members, obs = _synthetic_ensemble()
        summary = summaries.ensemble_summary(members)
        merged = summaries.merge_summary_with_obs(summary, obs)
        clim = climatology.climatology_table(members, obs)
        paths = plotting.plot_all_families(
            merged, clim, experiment="combined", site="FI-Hyy", variable="ET"
        )
        made = [p for v in paths.values() for p in v]
        assert all(Path(p).exists() for p in made)
        print(f"[OK] plotting — rendered {len(made)} files in {tmp_out}")
    finally:
        config.OUTPUT_ROOT = original_root
        config.OUTPUT_DIRS.update(original_dirs)
        # Attempt cleanup; swallow errors if the FS is read-only.
        try:
            shutil.rmtree(tmp_out, ignore_errors=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# 6  — NetCDF extraction smoke test
# ---------------------------------------------------------------------------
def _synthetic_netcdfs(dest: Path, n_members: int = 4, n_years: int = 2) -> None:
    """Create a tiny set of CLM-like NetCDFs so the extractor has something to chew on."""
    import xarray as xr
    levsoi = np.arange(20)
    for m in range(n_members):
        for yi, year in enumerate(range(2009, 2009 + n_years)):
            time = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
            n = len(time)
            ds = xr.Dataset(
                {
                    "QFLX_EVAP_TOT": (("time",), np.full(n, 1e-5, dtype=np.float32)),  # mm/s
                    "FSH":           (("time",), np.full(n, 50.0, dtype=np.float32)),
                    "NEE":           (("time",), np.full(n, -1.0, dtype=np.float32)),
                    "GPP":           (("time",), np.full(n, 5.0,  dtype=np.float32)),
                    "TLAI":          (("time",), np.full(n, 3.0,  dtype=np.float32)),
                    "H2OSOI":        (("time", "levsoi"),
                                      np.full((n, len(levsoi)), 0.3, dtype=np.float32)),
                },
                coords={"time": time, "levsoi": levsoi},
            )
            fname = f"clmoas.clm2_{m:04d}.h0.{year}-01-01-00000.nc"
            ds.to_netcdf(dest / fname)
            ds.close()


def check_extract_with_synthetic_nc() -> None:
    try:
        import xarray as xr  # noqa: F401
    except ImportError:
        print("[WARN] xarray missing — skipping NetCDF extractor check")
        return
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        # Fake "experiment/site" folder.
        src_site = tmp / "combined" / "FI-Hyy"
        src_site.mkdir(parents=True)
        _synthetic_netcdfs(src_site, n_members=4, n_years=2)

        # Monkey-patch config to point at the fixture.
        saved_base = config.MODEL_BASE_DIR
        saved_exp  = config.EXPERIMENT_DIR.copy()
        saved_root = config.OUTPUT_ROOT
        saved_dirs = config.OUTPUT_DIRS.copy()

        try:
            config.MODEL_BASE_DIR = tmp
            config.EXPERIMENT_DIR["combined"] = tmp / "combined"
            config.OUTPUT_ROOT = tmp / "evaluation"
            for k, v in saved_dirs.items():
                config.OUTPUT_DIRS[k] = config.OUTPUT_ROOT / k
                config.OUTPUT_DIRS[k].mkdir(parents=True, exist_ok=True)

            paths = extract.extract_site("combined", "FI-Hyy", force=True)
            assert paths, "extract_site returned nothing"
            et_csv = paths["ET"]
            df = io.read_wide_ensemble_csv(et_csv)
            # 2 years * 12 months = 24 rows; 4 members.
            assert len(df) == 24
            assert len([c for c in df.columns if c.startswith("real_")]) == 4
            # ET scale 86400 applied: QFLX_EVAP_TOT=1e-5 mm/s -> 0.864 mm/day
            val = df["real_0"].iloc[0]
            assert abs(val - 0.864) < 1e-3, f"ET scaling wrong: {val}"
            print(f"[OK] extractor — wrote {len(paths)} CSVs with ET={val:.3f} mm/d")
        finally:
            config.MODEL_BASE_DIR = saved_base
            config.EXPERIMENT_DIR.update(saved_exp)
            config.OUTPUT_ROOT = saved_root
            config.OUTPUT_DIRS.update(saved_dirs)


# ---------------------------------------------------------------------------
# 7  — composite figure smoke test
# ---------------------------------------------------------------------------
def check_composites() -> None:
    """Drop a tiny plot_inputs/metrics tree into a temp dir and render composites."""
    tmp_out = HERE / "_verify_tmp_composite"
    tmp_out.mkdir(exist_ok=True)
    original_root = config.OUTPUT_ROOT
    original_dirs = config.OUTPUT_DIRS.copy()
    try:
        config.OUTPUT_ROOT = tmp_out
        for k in config.OUTPUT_DIRS:
            config.OUTPUT_DIRS[k] = tmp_out / k
            config.OUTPUT_DIRS[k].mkdir(parents=True, exist_ok=True)

        # Synthesise plot_inputs for 3 sites x 1 experiment x 1 variable.
        exp = "combined"
        var = "ET"
        sites = ["FI-Hyy", "DE-Hai", "BE-Bra"]
        rng = np.random.default_rng(0)
        time = pd.date_range("2015-01-01", periods=24, freq="MS")
        for site in sites:
            signal = np.sin(np.arange(24) / 3.0) + 2.0  # deterministic model signal
            obs = signal + rng.normal(0, 0.2, 24)
            # pretend 2015 has no obs — model ensemble values are always present
            obs[:12] = np.nan
            # Model ensemble stats are independent of obs availability.
            mean = signal - 0.1
            lb = mean - 0.6
            ub = mean + 0.6
            q25 = mean - 0.2
            q75 = mean + 0.2
            merged = pd.DataFrame({
                "datetime": time,
                "mean": mean, "median": mean, "std": 0.3,
                "min": lb, "max": ub, "q25": q25, "q75": q75,
                "iqr": q75 - q25, "lb": lb, "ub": ub,
                "n_members": 128, "obs": obs,
            })
            io.write_csv(merged, config.plot_input_path(exp, site, var, "merged"))

            # Monthly climatology: model stats from full signal; obs_mean from
            # whichever year has valid obs (year 2016, months 12-23 here).
            clim_obs = np.nanmean(
                np.stack([obs[:12], obs[12:24]], axis=0), axis=0
            )  # NaN where both years missing, year-2 value otherwise
            clim = pd.DataFrame({
                "month": np.arange(1, 13),
                "mean": mean[:12], "min": lb[:12], "max": ub[:12],
                "q25": q25[:12], "q75": q75[:12],
                "obs_mean": clim_obs, "obs_std": np.full(12, 0.2),
            })
            io.write_csv(clim, config.plot_input_path(exp, site, var, "climatology"))

            site_metrics = pd.DataFrame([{
                "experiment": exp, "site": site, "variable": var,
                "all_CP": 95.5, "all_MBE": -0.1, "all_RMSE": 0.4,
                "all_ubRMSE": 0.3, "all_sigma": 0.3, "all_SS": 0.9,
                "growing_CP": 92.0, "growing_MBE": -0.1, "growing_RMSE": 0.4,
                "growing_ubRMSE": 0.3, "growing_sigma": 0.3, "growing_SS": 0.9,
            }])
            io.write_csv(site_metrics,
                         config.OUTPUT_DIRS["metrics"] / exp / f"{site}_metrics.csv")

        # Aggregated per-variable table
        agg = pd.DataFrame([
            {"experiment": exp, "site": s, "variable": var,
             "CP": 95.5, "MBE": -0.1, "RMSE": 0.4,
             "ubRMSE": 0.3, "sigma": 0.3, "SS": 0.9}
            for s in sites
        ])
        io.write_csv(agg, config.metric_path(exp, var, "all"))

        # Run the composite driver for ET only, combined only.
        paths_E = composite.plot_composite_spread_vs_obs(exp, var, sites=sites)
        paths_G = composite.plot_composite_iqr_mean_obs_spread(exp, var, sites=sites)
        paths_H = composite.plot_composite_climatology(exp, var, sites=sites)
        paths_I = composite.plot_all_experiments_grid(var, experiments=[exp], sites=sites)
        paths_J = composite.plot_coverage_heatmap(experiment=exp, scope="all")

        made = paths_E + paths_G + paths_H + paths_I + paths_J
        assert made, "no composite figures rendered"
        assert all(Path(p).exists() for p in made), "composite file missing on disk"
        print(f"[OK] composite plotting — rendered {len(made)} files")
    finally:
        config.OUTPUT_ROOT = original_root
        config.OUTPUT_DIRS.update(original_dirs)
        try:
            shutil.rmtree(tmp_out, ignore_errors=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("CLM5 pipeline self-check")
    print("=" * 70)
    try:
        check_imports()
        check_paths()
        check_observations()
        check_summaries_and_metrics()
        check_plotting()
        check_extract_with_synthetic_nc()
        check_composites()
    except AssertionError as exc:
        print(f"[FAIL] {exc}")
        return 1
    except Exception as exc:
        print(f"[FAIL] unhandled error: {exc!r}")
        raise
    print("-" * 70)
    print("All checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
