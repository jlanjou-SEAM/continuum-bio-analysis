# Provenance

## Runtime recovery

The exact `SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12.zip` used in the previous Famotidine v3.12 work was recovered from the project/library file store and materialized into the working container before this engineering archive was assembled.

Top-level recovered runtime ZIP SHA-256:

```text
e8d0d92587d802ca348524d1073ee2853c8c3fc2992072c6f5db9a288aaba704
```

Locked `data/prescreen.lock` SHA-256:

```text
62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4
```

The archive's own `VERIFY_LOCK.py` returned:

```text
LOCK VERIFY: PASS (29 locked files)
```

The bundled regression suite returned:

```text
11 passed
```

## Original experiment outputs

The previously generated dose-series package is retained unchanged under:

`07_original_captured_outputs/famotidine_ammonia_dose_series_v3_12.zip`

The previously generated 1 mg joint ledgers are retained under:

`07_original_captured_outputs/fam_ammonia_joint_1mg/`

## Independent reproduction

The engineering harness in `03_experiment_harness/` was then used to independently replay the same joint-state construction against the recovered locked runtime. The resulting dose-series summary agrees with the original captured summary to floating-point serialization precision; the maximum observed numeric difference after CSV round-tripping was below `2e-12`, with no categorical/string mismatches.
