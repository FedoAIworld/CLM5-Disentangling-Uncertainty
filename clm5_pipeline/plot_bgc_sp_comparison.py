"""
plot_bgc_sp_comparison.py
─────────────────────────
Generates CLM5-BGC vs CLM5-SP comparison bar charts (CP, MBE, RMSE)
for SM, SMr, ET, H, and GPP across ICOS flux-tower sites.

Each figure has three stacked panels:
  1. Coverage Percentage (CP, %)
  2. Mean Bias Error (MBE, variable units)
  3. Root Mean Square Error (RMSE, variable units)

Unit notes
----------
  SM / SMr : metrics CSV stores values in % volumetric water content.
             These are divided by 100 to convert to cm³ cm⁻³ before plotting.
  ET       : mm day⁻¹  
  H        : W m⁻²     
  GPP      : gC m⁻² d⁻¹

Site exclusions per variable
-----------------------------
  SM, SMr : SE-Svb excluded (limited)
  H       : DE-RuW excluded (poor/corrupt)

Usage
-----
    python plot_bgc_sp_comparison.py

Dependencies: numpy, matplotlib, pandas
"""

import os
import warnings
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

matplotlib.use('Agg')
warnings.filterwarnings('ignore')

# ── Paths ─────────────────────────────────────────────────────────────────────
BGC_DIR = '/p/scratch/cjicg41/eloundou1/CLM5_DATA/Archive/lnd/hist/Ensemble/evaluation/metrics/combined'
SP_DIR  = '/p/scratch/cjicg41/eloundou1/CLM5_DATA/Archive/lnd/hist/Ensemble/evaluation_sp/metrics/combined'
OUT_DIR = '/p/scratch/cjicg41/eloundou1/CLM5_DATA/Archive/lnd/hist/Ensemble/bgc_sp_comparison'

# ── Site lists (per variable) ─────────────────────────────────────────────────
VAR_SITES = {
    'SM':  ['FI-Hyy', 'CZ-BK1', 'DE-RuW', 'NL-Loo', 'FR-Pue', 'DE-Hai', 'DE-HoH', 'BE-Bra'],
    'SMR': ['FI-Hyy', 'CZ-BK1', 'DE-RuW', 'NL-Loo', 'FR-Pue', 'DE-Hai', 'DE-HoH', 'BE-Bra'],
    'ET':  ['FI-Hyy', 'SE-Svb', 'CZ-BK1', 'DE-RuW', 'NL-Loo', 'FR-Pue', 'DE-Hai', 'DE-HoH', 'BE-Bra'],
    'H':   ['FI-Hyy', 'SE-Svb', 'CZ-BK1', 'NL-Loo', 'FR-Pue', 'DE-Hai', 'DE-HoH', 'BE-Bra'],
    'GPP': ['FI-Hyy', 'SE-Svb', 'CZ-BK1', 'DE-RuW', 'NL-Loo', 'FR-Pue', 'DE-Hai', 'DE-HoH', 'BE-Bra'],
}

# ── Variable metadata ─────────────────────────────────────────────────────────
# scale : factor applied to MBE and RMSE (CP is always in %, no scaling)
#         SM/SMr: divide by 100 to convert % → cm³ cm⁻³
VARS = {
    'SM': {
        'label':    'Surface Soil Moisture (SM)',
        'unit':     r'$\mathrm{cm^3\ cm^{-3}}$',
        'scale':    1 / 100,
        'fmt_mbe':  '%.2f',
        'fmt_rmse': '%.2f',
    },
    'SMR': {
        'label':    'Root-Zone Soil Moisture (SMr)',
        'unit':     r'$\mathrm{cm^3\ cm^{-3}}$',
        'scale':    1 / 100,
        'fmt_mbe':  '%.2f',
        'fmt_rmse': '%.2f',
    },
    'ET': {
        'label':    'Evapotranspiration (ET)',
        'unit':     r'$\mathrm{mm\ d^{-1}}$',
        'scale':    1,
        'fmt_mbe':  '%.2f',
        'fmt_rmse': '%.2f',
    },
    'H': {
        'label':    'Sensible Heat Flux (H)',
        'unit':     r'$\mathrm{W\ m^{-2}}$',
        'scale':    1,
        'fmt_mbe':  '%.2f',
        'fmt_rmse': '%.2f',
    },
    'GPP': {
        'label':    'Gross Primary Production (GPP)',
        'unit':     r'$\mathrm{gC\ m^{-2}\ d^{-1}}$',
        'scale':    1,
        'fmt_mbe':  '%.2f',
        'fmt_rmse': '%.2f',
    },
}

# ── Colours ───────────────────────────────────────────────────────────────────
COL_BGC = '#2166AC'   # blue  — CLM5-BGC
COL_SP  = '#D6604D'   # red   — CLM5-SP


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_metrics(directory, site, variable):
    """Return (CP, MBE, RMSE) from the combined metrics CSV.

    Parameters
    ----------
    directory : str  path to the metrics/combined/ folder
    site      : str  ICOS site code
    variable  : str  variable name as stored in the CSV

    Returns
    -------
    tuple of (float | None, float | None, float | None)
        (all_CP, all_MBE, all_RMSE) — None when data are unavailable.
    """
    fpath = os.path.join(directory, f'{site}_metrics.csv')
    if not os.path.exists(fpath):
        return None, None, None
    df  = pd.read_csv(fpath)
    row = df[df['variable'] == variable]
    if row.empty:
        return None, None, None
    r = row.iloc[0]
    return r['all_CP'], r['all_MBE'], r['all_RMSE']


def add_bar_label(ax, bar_center, val, pad, fmt):
    """Place a bold value label above (positive) or below (negative) a bar."""
    if val is None:
        return
    y  = val + pad if val >= 0 else val - pad
    va = 'bottom'  if val >= 0 else 'top'
    ax.text(bar_center, y, fmt % val,
            ha='center', va=va,
            fontsize=9, color='#111111', fontweight='bold',
            clip_on=True)


# ── Main loop ─────────────────────────────────────────────────────────────────

for varname, vmeta in VARS.items():

    sites = VAR_SITES[varname]
    scale = vmeta['scale']
    n     = len(sites)
    x     = np.arange(n)
    w     = 0.35   # bar half-width

    fig, axes = plt.subplots(3, 1, figsize=(max(13, n * 1.35), 9.5))
    fig.patch.set_facecolor('white')

    # (metric_key, y-axis label, bar-label format, scaling factor)
    panel_info = [
        ('CP',   'Coverage Percentage (%)', '%.1f',            1),
        ('MBE',  f'MBE ({vmeta["unit"]})',  vmeta['fmt_mbe'],  scale),
        ('RMSE', f'RMSE ({vmeta["unit"]})', vmeta['fmt_rmse'], scale),
    ]

    for ai, (metric, ylabel, fmt_str, sc) in enumerate(panel_info):
        ax = axes[ai]
        ax.set_facecolor('#FAFAFA')

        # ── Collect and scale values ──
        bgc_vals, sp_vals = [], []
        for site in sites:
            cp_b, mbe_b, rmse_b = load_metrics(BGC_DIR, site, varname)
            cp_s, mbe_s, rmse_s = load_metrics(SP_DIR,  site, varname)
            raw_b = {'CP': cp_b, 'MBE': mbe_b, 'RMSE': rmse_b}[metric]
            raw_s = {'CP': cp_s, 'MBE': mbe_s, 'RMSE': rmse_s}[metric]
            bgc_vals.append(raw_b * sc if raw_b is not None else None)
            sp_vals.append( raw_s * sc if raw_s is not None else None)

        all_vals = [v for v in bgc_vals + sp_vals if v is not None]
        ymin = min(all_vals) if all_vals else 0
        ymax = max(all_vals) if all_vals else 1
        span = max(ymax - ymin, 1e-9)

        # ── Draw bars ──
        for i, (bv, sv) in enumerate(zip(bgc_vals, sp_vals)):
            if bv is not None:
                ax.bar(x[i] - w/2, bv, w,
                       color=COL_BGC, zorder=3, edgecolor='white', linewidth=0.5)
            if sv is not None:
                ax.bar(x[i] + w/2, sv, w,
                       color=COL_SP,  zorder=3, edgecolor='white', linewidth=0.5)

        # ── Bar value labels ──
        pad = span * 0.025
        for i, (bv, sv) in enumerate(zip(bgc_vals, sp_vals)):
            add_bar_label(ax, x[i] - w/2, bv, pad, fmt_str)
            add_bar_label(ax, x[i] + w/2, sv, pad, fmt_str)

        # ── Axes formatting ──
        ax.set_ylabel(ylabel, fontsize=13, labelpad=8)
        ax.set_xticks(x)
        ax.set_xticklabels(sites, fontsize=12, rotation=0)
        ax.axhline(0, color='#444444', linewidth=0.8, zorder=2)
        ax.grid(axis='y', linestyle='--', alpha=0.45, zorder=1, color='#AAAAAA')
        ax.tick_params(axis='y', labelsize=11)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        if metric == 'CP':
            ax.set_ylim(0, min(ymax * 1.22, 118))
        else:
            ax.set_ylim(ymin - span * 0.22, ymax + span * 0.22)

    # ── Figure title ──
    fig.suptitle(
        f'CLM5-BGC vs CLM5-SP  |  {vmeta["label"]}',
        fontsize=17, fontweight='bold', color='#023D6B',
        y=0.885,
    )

    # ── Legend ──
    patch_bgc = mpatches.Patch(color=COL_BGC, label='CLM5-BGC')
    patch_sp  = mpatches.Patch(color=COL_SP,  label='CLM5-SP')
    fig.legend(
        handles=[patch_bgc, patch_sp],
        loc='upper right',
        bbox_to_anchor=(0.999, 0.885),
        fontsize=12,
        framealpha=0.92,
        edgecolor='#CCCCCC',
        #title='Model',
        title_fontsize=11,
    )

    # ── Layout: top margin keeps title/legend clear of panels ──
    fig.subplots_adjust(
        hspace=0.62,
        left=0.09,
        right=0.985,
        top=0.80,
        bottom=0.07,
    )

    outpath = os.path.join(OUT_DIR, f'compare_{varname}.png')
    fig.savefig(outpath, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved: {outpath}')

print('\nAll figures generated successfully.')

