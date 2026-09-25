# SIDER_Prescreen_C

Locked minimal C implementation of the current SEAM/SIDER constitutive-closure prescreen runner.

## Runtime inputs

Exactly two external inputs:

```bash
./bin/sider_prescreen '<compound molecular formula>' '<dose>' [output_dir]
```

Example:

```bash
./bin/sider_prescreen C32H41NO2 '60 mg' output
```

The runtime does **not** require Python, NumPy, pandas, the JSON Manifold, or startup ablation passes.

## Dose model — locked correction

Dose is no longer encoded into the compound identity string.

The compound signature is fixed by molecular formula alone:

```text
Q = surface_signature("COMPOUND_FORMULATION:<formula>")
```

The supplied mass dose is converted to a continuous molecule-count-proportional loading coordinate:

```text
molecular_weight = sum(element_count * atomic_weight)
loading_mmol     = dose_mg / molecular_weight_g_mol
```

For structure `i`:

```text
C_i(lambda) = normalize(clip(T_i + lambda * (Q - G), EPS))
lambda      = loading_mmol
```

This gives dose an ordered continuous role while leaving compound identity unchanged.

Supported dose units: `mg`, `g`, `ug`, `mcg`, `ng`.

The molecular formula must be a parseable empirical formula using the elements implemented in `src/sider_prescreen.c`.

### Required invariants

- `0 mg` must reproduce the structure-only baseline exactly.
- Increasing dose must never be implemented as a different compound identity.
- For a fixed compound, constitutive-relation breaks must be evaluated from the same `Q` at every dose.

The current terfenadine validation gives zero closure hits at `0 mg` and no row-level broken-relation reversals over `0, 30, 60, 90, 120, 150, 180, 240, 300 mg`.

## Locked data

`data/prescreen.lock` contains the compound-independent state frozen from the validated structure-only implementation:

- 232 Manifold entry surfaces;
- the 128-dimensional Manifold mean `G`;
- 420 unique structure-only signatures `T`;
- baseline localization identity for every unique structure;
- all ablation-derived constitutive relation sets;
- mapping back to all 5,734 two-column rows and their provenance strings.

The human-readable active matrix is retained as `data/SEAM_BASELINES_5734_TWO_COLUMN.csv` for audit. It is not parsed during the C run.

## Constitutive closure and tiers

For each unique structure, the engine compares its locked constitutive relations against `C_i(lambda)` and expands the result back to all 5,734 individual rows.

```text
NONE      broken = 0
LOW       0 < b/r <= 0.25
MEDIUM    0.25 < b/r <= 0.50
HIGH      0.50 < b/r < 1
CRITICAL  b/r = 1
```

`closure_load` remains:

```text
(broken / total) * ln(1 + total)
```

It is a structural loading measure, not a clinical incidence percentage.

## Outputs

- `results_all_5734.csv` — every matrix row in baseline order;
- `hits_tiered.csv` — closure-positive rows sorted by tier, closure load, then baseline ID;
- `summary.json` — counts, molecular weight, dose in mg, continuous loading in mmol, and runtime information.

## Build

Linux/macOS with a C11 compiler:

```bash
make
```

Only the C standard library and `libm` are required.

The included `bin/sider_prescreen` is the Linux x86-64 build produced for validation; rebuild from source for another platform.

## Lock status

The closure cache remains a build artifact. A change to the Manifold, two-column matrix, surface signature, structure-only baseline rule, ablation rule, relation tolerance, closure-load equation, tier boundaries, **or dose-loading equation** requires validation before relocking the distribution.
