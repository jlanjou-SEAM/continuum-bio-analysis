# Engineering record — SIDER_Prescreen_C 1.1.0-dose-load

## Purpose

The minimal C runtime retains the locked structure-only constitutive-closure engine while correcting dose from an identity token into a continuous loading variable.

The previous C/Python-compatible implementation formed:

```text
Q_old = signature("COMPOUND_FORMULATION:<formula>|DOSE:<dose>")
C_old = normalize(clip(T + (Q_old - G)))
```

That representation made `60 mg`, `120 mg`, and `180 mg` different encoded identities. It had no mathematical requirement that increasing dose produce an ordered increase in perturbation.

Version `1.1.0-dose-load` removes dose from `Q` and applies dose as the scalar amplitude of one fixed compound perturbation.

## Frozen structural state

The binary lock is unchanged in structural content. It contains:

- 5,734 row identities;
- 420 unique structures;
- 128 surface dimensions;
- 232 retained Manifold surfaces;
- 54,205 constitutive coordinate-pair relations;
- 3,404 necessary-coordinate references before pair expansion;
- each structure-only target vector `T`;
- each structure's baseline Manifold localization index;
- row-to-structure mapping and source/deviation metadata.

The source term is provenance only. It never enters the compound resolution math.

## Compound identity

The 128-dimensional compound vector is generated from molecular formula only:

```text
Q = signature("COMPOUND_FORMULATION:<formula>")
```

The signature algorithm is unchanged:

1. Base64-encode the UTF-8 bytes without `=` padding.
2. Measure normalized symbol composition over the 64-symbol alphabet.
3. Measure normalized absolute differences of adjacent Base64 symbol indices.
4. Concatenate the two 64-element vectors.
5. Normalize the 128-element state.

## Continuous dose loading

The mass dose is parsed independently of compound identity and converted to millimoles:

```text
MW     = molecular weight of supplied empirical formula, g/mol
mg     = supplied dose converted to milligrams
lambda = mg / MW
```

Because `mg / (g/mol) = mmol`, `lambda` is proportional to the number of supplied molecules for the fixed compound.

Runtime state for structure `i`:

```text
raw_i(lambda) = T_i + lambda * (Q - G)
C_i(lambda)   = normalize(clip(raw_i(lambda), EPS))
EPS           = 1e-15
```

This is a loading coordinate, not a pharmacokinetic plasma-concentration model. It does not currently incorporate absorption, bioavailability, clearance, protein binding, or distribution volume.

## Why the loading is ordered

For any pair of surface coordinates `a,b`, before clipping and common normalization:

```text
raw_a(lambda) - raw_b(lambda)
 = (T_a - T_b)
 + lambda * [(Q_a-G_a) - (Q_b-G_b)]
```

This is affine in `lambda`. A baseline ordering relation can therefore cross its boundary at most once as loading increases, absent clipping degeneracy. The validation grid explicitly checks that broken-relation counts never decrease row-by-row.

## Constitutive closure

Necessary coordinates and baseline pair relations remain frozen from the structure-only ablation pass. Runtime relation comparison retains the `1e-12` equality tolerance.

The five structural marker classes remain unchanged:

```text
NONE      b = 0
LOW       0 < b/r <= 0.25
MEDIUM    0.25 < b/r <= 0.50
HIGH      0.50 < b/r < 1
CRITICAL  b/r = 1
```

`closure_load` remains:

```text
(b/r) * ln(1+r)
```

## Dose-model validation

### Zero-dose invariant

Terfenadine `C32H41NO2` at `0 mg`:

```text
rows                         5,734
closure-hit rows                 0
NONE                         5,734
baseline localization kept  5,734 / 5,734
```

Thus `lambda=0` reproduces the unperturbed structure-only state.

### Terfenadine dose grid

Tested at:

```text
0, 30, 60, 90, 120, 150, 180, 240, 300 mg
```

Across every transition in this grid:

```text
row-level decreases in broken constitutive-relation count = 0
```

Aggregate broken-relation counts rose monotonically:

```text
0 mg        0
30 mg   56,834
60 mg   61,265
90 mg   68,290
120 mg  77,041
150 mg  85,734
180 mg  94,055
240 mg 108,304
300 mg 123,871
```

Known QT/torsades/ventricular-arrhythmia structure (`21` constitutive relations) followed:

```text
0 mg    0/21  NONE
30 mg   3/21  LOW
60 mg   3/21  LOW
90 mg   3/21  LOW
120 mg  4/21  LOW
150 mg  5/21  LOW
180 mg  5/21  LOW
240 mg  8/21  MEDIUM
300 mg  8/21  MEDIUM
```

Sudden-death structure (`496` relations):

```text
0 mg      0/496  NONE
30 mg    55/496  LOW
60 mg    63/496  LOW
90 mg    75/496  LOW
120 mg   79/496  LOW
150 mg   86/496  LOW
180 mg   95/496  LOW
240 mg  109/496  LOW
300 mg  125/496  MEDIUM
```

### Runtime regression

All ten previously used molecular formulas parse successfully under the dose-loading model and complete the full 5,734-row test using the locked C engine.

## Runtime performance

The corrected runtime remains approximately 0.2–0.3 seconds for a complete 5,734-row run in the current environment, including cache loading and CSV generation.

## Interpretation limit

The corrected loading term establishes ordered chemical amount. It does **not** claim that oral mass dose equals tissue concentration. Any future PK/PD layer must be added explicitly rather than hidden inside the loading scalar.
