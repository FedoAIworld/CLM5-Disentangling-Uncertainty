#!/bin/bash
# ---------------------------------------------------------------------------
# submit_jsc_aggregate.sh — aggregate per-site metric CSVs into per-experiment
# tables once all array tasks from submit_jsc.sh have finished.
#
# Submit with a dependency on the main array:
#
#     ARRAY_ID=$(sbatch --parsable submit_jsc.sh)
#     sbatch --dependency=afterok:${ARRAY_ID} submit_jsc_aggregate.sh
# ---------------------------------------------------------------------------
#SBATCH --job-name=clm5_eval_agg
#SBATCH --account=jicg41
#SBATCH --partition=dc-cpu
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=128
#SBATCH --time=02:00:00
#SBATCH --output=logs/clm5_eval_agg_%j.out
#SBATCH --error=logs/clm5_eval_agg_%j.err

set -euo pipefail

# SLURM copies the batch script to a spool dir; use SLURM_SUBMIT_DIR (where
# sbatch was invoked) for the real pipeline path.
if [[ -n "${SLURM_SUBMIT_DIR:-}" ]]; then
    PIPELINE_DIR="${SLURM_SUBMIT_DIR}"
else
    PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

source "${PIPELINE_DIR}/modules.sh"
export PYTHONPATH="${PIPELINE_DIR}/..:${PYTHONPATH:-}"
mkdir -p "${PIPELINE_DIR}/logs"
export CLM5_MODEL_BASE_DIR="${CLM5_MODEL_BASE_DIR:-/p/scratch/cjicg41/eloundou1/CLM5_DATA/Archive/lnd/hist/Ensemble}"
export CLM5_OBS_DIR="${CLM5_OBS_DIR:-/p/scratch/cjicg41/eloundou1/Observations/ICOS_data}"

# Inherit mode from launcher (or default to bgc).
export CLM5_PIPELINE_MODE="${CLM5_PIPELINE_MODE:-bgc}"

if [[ "${CLM5_PIPELINE_MODE}" == "sp" ]]; then
    export CLM5_EVAL_OUTPUT_ROOT="${CLM5_EVAL_OUTPUT_ROOT:-${CLM5_MODEL_BASE_DIR}/evaluation_sp}"
else
    export CLM5_EVAL_OUTPUT_ROOT="${CLM5_EVAL_OUTPUT_ROOT:-${CLM5_MODEL_BASE_DIR}/evaluation}"
fi

cd "${PIPELINE_DIR}"

python run_pipeline.py \
    --mode "${CLM5_PIPELINE_MODE}" \
    --aggregate-only \
    --repair-missing \
    --workers "${REPAIR_WORKERS:-4}" \
    --log-level INFO \
    "$@"

echo "DONE aggregate/repair/composites @ $(date -Is)"
