"""clm5_pipeline — ensemble evaluation pipeline for CLM5.

The package exposes two sub-packages:

* ``config`` with site/variable/path constants.
* ``pipeline`` with the per-stage implementations (extract, derive,
  observations, summaries, metrics, climatology, plotting, runner).

Run it from the CLI via ``run_pipeline.py``.
"""

__all__ = ["config", "pipeline"]
