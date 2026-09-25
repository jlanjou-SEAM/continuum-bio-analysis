# Method

## 1. Locked engine

The experiment uses `SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12` unchanged.

The v3.12 runtime has three ordinary external inputs for a single chemical:

1. compound name or empirical formula;
2. dose per administration;
3. interval.

For this experiment, the existing single-compound perturbation operator was used as the engine boundary and a joint chemical projection was constructed **outside** the locked engine. No engine equation, database record, constitutive relation, biological row, criticality rule, or pair-resolution rule was edited.

## 2. Single-compound projection

For each empirical formula the locked engine constructs a 128-coordinate projection `Q` using `surface_signature(formula)` and localizes it against the retained Manifold surfaces.

Famotidine:

- formula: `C8H15N7O2S3`
- dose: `40 mg`
- interval: `once daily`
- molecular mass used by v3.12: `337.4454 g/mol`
- loading: `0.11853769528344439 mmol/day`

Ammonia:

- formula: `NH3`
- interval used in the model: `once daily`
- molecular mass used by v3.12: `17.03052 g/mol`
- retained-burden coordinates tested: `0, 0.1, 0.25, 0.5, 1, 2, 5 mg/day`

The NH3 values are model coordinates representing retained burden for the experiment. They are not administered-dose recommendations.

## 3. Existing v3.12 row-wise operator

For biological condition row `j`, v3.12 constructs a condition state `B_j` from:

```text
structure + structural_deviation
```

The source/condition label is provenance only and is excluded from the structural state.

The locked response operator is:

```text
R_j = normalize(clip(B_j + L*(Q - G), EPS))
```

where:

- `B_j` = independently represented condition state;
- `Q` = 128-coordinate chemical projection;
- `G` = locked global reference vector;
- `L` = exposure/loading coordinate in mmol/day;
- `R_j` = normalized perturbed state.

The engine executes all 5,734 rows independently against their locked parent constitutive templates.

## 4. Joint-state construction

For famotidine loading `L_F`, projection `Q_F`, ammonia loading `L_A`, and projection `Q_A`, the harness defines:

```text
L_joint = L_F + L_A

Q_joint = (L_F*Q_F + L_A*Q_A) / L_joint
```

The unchanged engine then receives `Q_joint` and `L_joint`.

This preserves the existing v3.12 perturbation equation because:

```text
L_joint*(Q_joint - G)
= L_F*(Q_F - G) + L_A*(Q_A - G)
```

Therefore the pre-normalization state is exactly:

```text
B_j + L_F*(Q_F-G) + L_A*(Q_A-G)
```

There is no fitted cross-term, interaction coefficient, clinical label, or manually inserted expected answer.

## 5. Constitutive transition accounting

For each row, v3.12 compares the perturbed response state with the locked parent constitutive relations and records:

- initial broken relations;
- relations restored;
- new relations broken;
- residual broken relations;
- relation transition count;
- initial offset from reference;
- residual offset;
- net and absolute offset change;
- direction toward/away from reference;
- criticality from new-break fraction.

## 6. Pair resolution

After row-wise perturbation, v3.12 computes the existing pair-correspondence decoder:

```text
pair = 0.82 * JS_similarity(Q, B_j)
     + 0.18 * sign_continuity(Q, B_j)
```

For the joint experiment, `Q` is `Q_joint`.

Pair resolution cannot create a structural hit. A row enters pair ranking only when the row-wise perturbation already produced `relation_transition_count > 0`.

## 7. Frozen speech/language cohort

The cohort was selected structurally, not by post-hoc outcome magnitude. The filter was:

```text
structure contains "language-processing" OR "speech-planning"
```

This produced 17 baseline rows, frozen across every dose:

`SB0379, SB1656, SB1666, SB1669, SB1679, SB1929, SB3035, SB3473, SB4329, SB4609, SB4932, SB4934, SB4968, SB4969, SB4970, SB5058, SB5705`.

All comparisons use the same 17 rows at every NH3 burden.
