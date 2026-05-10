"""CLM5 ensemble evaluation pipeline.

Modules
-------
io            NetCDF / CSV loading helpers (wraps legacy helper_funcs).
extract       Per (experiment, site) extraction to monthly ensemble CSVs.
derive        H2OSOI -> SM / SMR derivation and ET / SM unit conversion.
observations  Load and align monthly observations (ET/H/NEE/GPP/SM/SMR/LAI).
summaries     Ensemble summary statistics (mean/median/q25/q75/IQR/...).
metrics       CP, MBE, RMSE, ubRMSE, spread sigma and SS (Eqs. 2-7).
climatology   Monthly climatology (model-only and model-vs-obs).
plotting      Four plot families (PDF + PNG) for every variable incl. SMR.
runner        Orchestrates full pipeline per (experiment, site).
"""

__all__ = [
    "io",
    "extract",
    "derive",
    "observations",
    "summaries",
    "metrics",
    "climatology",
    "plotting",
    "runner",
]
