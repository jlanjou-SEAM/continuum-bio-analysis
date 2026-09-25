# Reproduction Instructions

## Requirements

Use a Python environment capable of running the bundled v3.12 requirements. The locked runtime contains its own `requirements.txt` and regression tests.

## One-command reproduction

From the archive root:

```bash
bash 03_experiment_harness/run_all.sh
```

The command performs:

1. `python VERIFY_LOCK.py`
2. `python -m pytest -q tests/test_full_runtime.py`
3. the complete joint dose series via `run_joint_dose_series.py`

## Direct experiment invocation

```bash
python 03_experiment_harness/run_joint_dose_series.py \
  --runtime 02_runtime_extracted/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12 \
  --out 04_results/new_reproduction
```

To run selected NH3 burden coordinates:

```bash
python 03_experiment_harness/run_joint_dose_series.py \
  --runtime 02_runtime_extracted/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12 \
  --out /tmp/seam_joint \
  --nh3-doses 0,0.1,1,5
```

## Verification targets

Expected locked-runtime checks:

```text
LOCK VERIFY: PASS (29 locked files)
11 passed
```

Reference integrity values are stored in `06_verification/` and `SHA256SUMS.txt`.
