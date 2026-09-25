# Analysis contract - v3.12 row-wise perturbation + restored pair resolution

- This package produces structural analysis output only.
- External inputs are compound/formula, dose, and interval.
- Named compound input is resolved through `data/compound_registry.json`; direct empirical formulas remain valid.
- Every accepted compound is resolved to one 128-coordinate Manifold projection before biological execution.
- Dose and interval affect exposure/loading only and do not alter compound identity.
- The biological matrix contains 5,734 condition/deviation rows mapped to 420 locked constitutive reference templates.
- **Each of the 5,734 rows is perturbed independently.** A result computed for one of the 420 parent templates is never copied or expanded to its mapped rows.
- Each row's condition state is constructed from `structure + structural_deviation`. `source_term` is provenance/reporting only and does not enter the structural state, so aliases with the same represented structure/deviation remain aliases.
- For row `j`, the current compound perturbs only that row's condition state: `R_j = normalize(clip(B_j + lambda*(Q-G), EPS))`.
- The row is compared to its locked parent constitutive reference to count initial broken relations, relations restored by the compound perturbation, new breaks introduced by the compound, residual broken relations, and net offset change.

## Restored pair-resolution stage

After the 5,734 row-wise perturbation results exist, the current compound state is evaluated against each independently represented condition state using the restored v3.7 pair-correspondence operator:

`pair_correspondence_j = 0.82 * JS_similarity(Q, B_j) + 0.18 * sign_continuity(Q, B_j)`

where `Q` is the current compound Manifold projection and `B_j` is the row's represented biological condition state.

- Pair resolution is a **decoder of the current compound/condition relation**, not a second perturbation run.
- Pair correspondence **cannot create a hit**. A row is eligible for primary/secondary effect ranking only when the row-wise perturbation already produced `relation_transition_count > 0`.
- Pair score does not replace or multiply the saved perturbation evidence. Restored relations, new breaks, residual relations, offset direction, and criticality remain independent evidence attached to the pair-resolved row.
- Primary/secondary ordering is **within the current compound run only**. No other compound is used for ranking, similarity, overlap, validation, or interpretation.
- Active rows are ranked deterministically by pair correspondence descending; baseline ID breaks exact ties.
- Criticality is based only on the fraction of locked parent constitutive relations newly broken by this compound perturbation: INFORMATIONAL / MINOR / MODERATE / HIGH / CRITICAL.
- No drug indication, known side-effect list, consumer label, or clinical outcome database enters the perturbation, pair resolver, ranking, or criticality calculation.

## Required audit chain

1. `process/01_compound_resolution.json`
2. `process/02_compound_manifold_projection.json`
3. `process/03_exposure_resolution.json`
4. `process/04_rowwise_condition_comparison.json`
5. `process/05_pair_resolution.json`
6. `full_sider_raw/results_all_5734.csv`
7. `full_sider_raw/pair_ranked_active_hits.csv`
8. `result.json`
9. generated PDF report
