#!/bin/bash
# ---------------------------------------------------------------------------
# submit_jsc_full.sh — one-command launcher for the CLM5 evaluation pipeline.
#
# Usage from the pipeline directory:
#
#   BGC mode (default) — 4 experiments × 14 sites → 56 array tasks
#     bash submit_jsc_full.sh
#     bash submit_jsc_full.sh --force
#
#   SP mode — 1 experiment (combined) × 9 sites → 9 array tasks
#     bash submit_jsc_full.sh --mode sp
#     bash submit_jsc_full.sh --mode sp --force
#
# Any flag other than --mode is forwarded to run_pipeline.py.
#
# The script submits the site-processing array, then a repair/aggregate/
# composite job with afterany dependency. afterany is intentional: if a
# compute node fails, the dependent job still starts and repairs missing
# site outputs.
# ---------------------------------------------------------------------------
set -euo pipefail

PIPELINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PIPELINE_DIR}"
mkdir -p logs

# ---------------------------------------------------------------------------
# Parse --mode from the argument list (default: bgc).
# All other flags are forwarded to the array job as-is.
# ---------------------------------------------------------------------------
MODE="${CLM5_PIPELINE_MODE:-bgc}"
PASS_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"; shift 2 ;;
        --mode=*)
            MODE="${1#--mode=}"; shift ;;
        *)
            PASS_ARGS+=("$1"); shift ;;
    esac
done

if [[ "${MODE}" != "bgc" && "${MODE}" != "sp" ]]; then
    echo "error: --mode must be 'bgc' or 'sp', got '${MODE}'" >&2
    exit 1
fi

# Propagate mode to child scripts via environment variable.
export CLM5_PIPELINE_MODE="${MODE}"

# Array range: BGC = 0-55 (4×14), SP = 0-8 (1×9).
if [[ "${MODE}" == "sp" ]]; then
    ARRAY_RANGE="0-8"
    echo "Mode: SP  (combined × 9 sites, ${ARRAY_RANGE} array tasks)"
else
    ARRAY_RANGE="0-55"
    echo "Mode: BGC (4 experiments × 14 sites, ${ARRAY_RANGE} array tasks)"
fi

# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------
ARRAY_ID=$(sbatch --parsable --array="${ARRAY_RANGE}" \
               submit_jsc.sh "${PASS_ARGS[@]+"${PASS_ARGS[@]}"}")
echo "Submitted site array: ${ARRAY_ID}"

AGG_ID=$(sbatch --parsable --dependency=afterany:${ARRAY_ID} \
             submit_jsc_aggregate.sh "${PASS_ARGS[@]+"${PASS_ARGS[@]}"}")
echo "Submitted repair/aggregate/composite job: ${AGG_ID}"
echo "Pipeline submitted. Final figures will be produced by job ${AGG_ID}."

