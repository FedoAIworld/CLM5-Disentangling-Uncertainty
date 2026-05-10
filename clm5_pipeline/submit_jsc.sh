#!/bin/bash
# ---------------------------------------------------------------------------
# submit_jsc.sh — SLURM wrapper to run the full CLM5 evaluation pipeline
#                 on JSC (JURECA / JUWELS) in one shot.
#
# Supports two pipeline modes via CLM5_PIPELINE_MODE (set by the launcher):
#
#   bgc (default)  4 experiments × 14 sites → 56 array tasks (0-55)
#   sp             1 experiment  ×  9 sites →  9 array tasks (0-8)
#
# The --array range is overridden by the launcher (submit_jsc_full.sh);
# the #SBATCH directive below is the fallback for manual sbatch calls.
#
# Usage (via launcher — recommended):
#     bash submit_jsc_full.sh              # BGC
#     bash submit_jsc_full.sh --mode sp    # SP
#
# Manual submission (BGC):
#     sbatch submit_jsc.sh
# Manual submission (SP):
#     export CLM5_PIPELINE_MODE=sp
#     sbatch --array=0-8 submit_jsc.sh
# ---------------------------------------------------------------------------
#SBATCH --job-name=clm5_eval
#SBATCH --account=jicg41
#SBATCH --partition=dc-cpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128
#SBATCH --time=02:00:00
#SBATCH --array=0-55                      # overridden to 0-8 for SP by launcher
#SBATCH --output=logs/clm5_eval_%A_%a.out
#SBATCH --error=logs/clm5_eval_%A_%a.err

set -euo pipefail

# ---------------------------------------------------------------------------
# Resolve paths first so everything else is absolute.
# ---------------------------------------------------------------------------
if [[ -n "${SLURM_SUBMIT_DIR:-}" ]]; then
    PIPELINE_DIR="${SLURM_SUBMIT_DIR}"
else
    PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
source "${PIPELINE_DIR}/modules.sh"
export PYTHONPATH="${PIPELINE_DIR}/..:${PYTHONPATH:-}"

mkdir -p "${PIPELINE_DIR}/logs"

# Paths (override by exporting before sbatch).
export CLM5_MODEL_BASE_DIR="${CLM5_MODEL_BASE_DIR:-/p/scratch/cjicg41/eloundou1/CLM5_DATA/Archive/lnd/hist/Ensemble}"
export CLM5_OBS_DIR="${CLM5_OBS_DIR:-/p/scratch/cjicg41/eloundou1/Observations/ICOS_data}"

# Pipeline mode — set by launcher or manually before sbatch.
export CLM5_PIPELINE_MODE="${CLM5_PIPELINE_MODE:-bgc}"

# Separate output roots keep BGC and SP results independent.
if [[ "${CLM5_PIPELINE_MODE}" == "sp" ]]; then
    export CLM5_EVAL_OUTPUT_ROOT="${CLM5_EVAL_OUTPUT_ROOT:-${CLM5_MODEL_BASE_DIR}/evaluation_sp}"
else
    export CLM5_EVAL_OUTPUT_ROOT="${CLM5_EVAL_OUTPUT_ROOT:-${CLM5_MODEL_BASE_DIR}/evaluation}"
fi

mkdir -p "${CLM5_EVAL_OUTPUT_ROOT}"

# ---------------------------------------------------------------------------
# Map SLURM_ARRAY_TASK_ID → (experiment, site)
# Mode-specific lists must match config.py EXPERIMENTS_BGC/SP and SITES_BGC/SP.
# ---------------------------------------------------------------------------
if [[ "${CLM5_PIPELINE_MODE}" == "sp" ]]; then
    EXPERIMENTS=(combined)
    SITES=(FI-Hyy SE-Svb CZ-BK1 DE-RuW NL-Loo FR-Pue DE-Hai DE-HoH BE-Bra)
else
    EXPERIMENTS=(forcing soil vegetation combined)
    SITES=(FI-Hyy FI-Sod SE-Svb CZ-BK1 DE-Obe DE-RuW IT-Lav NL-Loo \
           ES-Cnd FR-Pue DE-Hai DE-HoH DK-Vng BE-Bra)
fi

N_SITES=${#SITES[@]}
TASK_ID=${SLURM_ARRAY_TASK_ID:-0}
EXP_INDEX=$(( TASK_ID / N_SITES ))
SITE_INDEX=$(( TASK_ID % N_SITES ))
EXPERIMENT="${EXPERIMENTS[$EXP_INDEX]}"
SITE="${SITES[$SITE_INDEX]}"

echo "=========================================================="
echo " SLURM_JOB_ID     = ${SLURM_JOB_ID:-local}"
echo " SLURM_ARRAY_ID   = ${SLURM_ARRAY_JOB_ID:-local}"
echo " TASK             = ${TASK_ID} -> ${EXPERIMENT} / ${SITE}"
echo " OUTPUT_ROOT      = ${CLM5_EVAL_OUTPUT_ROOT}"
echo " WORK             = $(pwd)"
echo "=========================================================="

# ---------------------------------------------------------------------------
# Run the pipeline
# ---------------------------------------------------------------------------
cd "${PIPELINE_DIR}"
python run_pipeline.py \
    --mode "${CLM5_PIPELINE_MODE}" \
    --experiment "${EXPERIMENT}" \
    --site "${SITE}" \
    --workers 1 \
    --log-level INFO \
    "$@"

echo "DONE ${EXPERIMENT}/${SITE} @ $(date -Is)"
