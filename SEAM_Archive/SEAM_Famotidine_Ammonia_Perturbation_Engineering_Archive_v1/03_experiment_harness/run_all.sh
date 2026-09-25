#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
RUNTIME="$HERE/02_runtime_extracted/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12"
OUT="$HERE/04_results/reproduced_dose_series"
cd "$RUNTIME"
python VERIFY_LOCK.py | tee "$HERE/06_verification/VERIFY_LOCK.txt"
python -m pytest -q tests/test_full_runtime.py | tee "$HERE/06_verification/PYTEST.txt"
rm -rf "$OUT"
python "$HERE/03_experiment_harness/run_joint_dose_series.py" --runtime "$RUNTIME" --out "$OUT" | tee "$HERE/06_verification/EXPERIMENT_STDOUT.json"
