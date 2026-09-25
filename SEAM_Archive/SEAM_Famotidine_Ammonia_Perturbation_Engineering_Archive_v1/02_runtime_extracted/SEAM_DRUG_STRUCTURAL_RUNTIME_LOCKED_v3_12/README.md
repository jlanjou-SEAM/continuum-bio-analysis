# SEAM Drug Structural Runtime v3.12 - 5,734 independent perturbations + restored pair resolution

v3.12 keeps the corrected v3.11 multi-compound execution and restores the pair-correspondence decoder that was present in the earlier comparison architecture.

The two stages answer different questions:

1. **Perturbation:** what does this compound do to each represented biological condition state?
2. **Pair resolution:** which of those already-active structural transitions most directly correspond to this compound's resolved structural state?

Pair resolution never creates a structural hit and never reruns the 5,734 perturbations.

## Three inputs

1. compound name or direct empirical formula
2. dose per administration
3. interval

## Runtime path

```text
compound/formula
  -> compound registry/formula resolution
  -> 128-coordinate compound Manifold projection Q
  -> dose + interval loading coordinate
  -> for each of 5,734 condition/deviation rows independently:
       construct B_j from structure + structural deviation
       apply current compound perturbation -> R_j
       measure restored relations, new breaks, residual state, offset and direction
  -> restored pair resolution for every row:
       Q x B_j
       pair = 0.82*JS + 0.18*sign continuity
  -> hit gate: relation_transition_count > 0
  -> rank active hits by pair correspondence within THIS compound run only
  -> primary / secondary structural responses
  -> PDF + complete CSV/JSON trace
```

The 420 structure records remain constitutive reference templates only. They are not the unit of execution.

## Audit outputs

- `process/01_compound_resolution.json`
- `process/02_compound_manifold_projection.json`
- `process/03_exposure_resolution.json`
- `process/04_rowwise_condition_comparison.json`
- `process/05_pair_resolution.json`
- `full_sider_raw/results_all_5734.csv`
- `full_sider_raw/pair_ranked_active_hits.csv`
- `result.json`
- generated PDF report

No cross-compound overlap or similarity metric is part of this runtime.
