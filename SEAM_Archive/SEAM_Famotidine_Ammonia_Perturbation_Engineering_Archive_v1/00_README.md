# SEAM Famotidine + Ammonia Perturbation Engineering Archive

## Purpose

This archive captures the complete reproducible engineering record for the SEAM v3.12 perturbation cause-and-effect assessment in which a fixed famotidine exposure was evaluated alone and then as a joint chemical state with a declared retained-ammonia burden.

The archive preserves:

- the exact locked v3.12 runtime used for the work;
- an extracted, readable copy of that runtime and its source;
- lock and regression-test verification;
- the joint-state construction and its mathematical derivation;
- a standalone experiment harness that does not modify the locked engine;
- the famotidine-only and ammonia-only control runs;
- the full 5,734-row joint-state ledgers for every tested ammonia burden;
- pair-ranked active-hit ledgers;
- the frozen 17-row language/speech structural cohort;
- dose-series summaries and original captured output package;
- SHA-256 inventory and reproducibility checks.

## Core result captured

With famotidine fixed at 40 mg once daily, increasing the declared NH3 retained-burden coordinate from 0 to 5 mg/day increased the mean absolute displacement of the frozen language/speech structural family from 0.0185128139 to 0.1468991860. The same family accumulated additional constitutive relation breaks and moved upward in the within-run pair ranking.

This is a **perturbation cause-and-effect assessment inside the v3.12 structural model**. It is not a claim that ammonia is the singular clinical or etiological cause of any reported adverse event, and the NH3 burden coordinates are not dosing recommendations.

## Archive layout

- `01_original_runtime/` — exact locked v3.12 ZIP as recovered.
- `02_runtime_extracted/` — extracted engine, data, C source/binary, reports, tests, and lock files.
- `03_experiment_harness/` — joint-state runner and one-command reproduction script.
- `04_results/` — controls and complete reproduced dose-series ledgers.
- `05_engineering_record/` — method, equations, pipeline, design decisions, and result interpretation.
- `06_verification/` — lock verification, test output, reproducibility comparison, environment record.
- `07_original_captured_outputs/` — the previously produced dose-series package and 1 mg joint-run outputs retained unchanged.
- `SHA256SUMS.txt` — integrity manifest for all files in this archive.

## Reproduction

From the archive root on a system with Python and the runtime requirements available:

```bash
bash 03_experiment_harness/run_all.sh
```

The script first verifies the locked engine, executes its regression tests, and then performs the joint famotidine/NH3 dose series without editing the engine.
