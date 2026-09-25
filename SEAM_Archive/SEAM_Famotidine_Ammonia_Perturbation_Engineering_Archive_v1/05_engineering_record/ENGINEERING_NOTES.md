# Engineering Notes

## Frozen components

The following are taken directly from the locked v3.12 package and were not edited for this experiment:

- `data/prescreen.lock`
- 5,734 biological condition/deviation rows
- 420 constitutive parent templates
- retained Manifold surfaces and reference vector
- empirical-formula surface projection function
- molecular-weight table
- row-wise perturbation equation
- constitutive relation comparison
- criticality thresholds
- Jensen-Shannon calculation
- pair-correspondence equation and ranking rule
- report/PDF code

## Experiment-specific component

The only new calculation is the joint-state adapter in:

`03_experiment_harness/run_joint_dose_series.py`

It composes two already-resolved chemical projections using their loading coordinates and hands the resulting projection/loading pair to the unchanged v3.12 row-wise engine.

## Why loading is in mmol/day

The v3.12 runtime converts dose and interval to daily-equivalent mass and divides by the molecular mass. Consequently the perturbation loading coordinate is amount-of-substance per day rather than raw mass. This is why 1 mg/day NH3 is a substantial fraction of the joint loading relative to 40 mg/day famotidine: the molecules have very different molecular masses.

## 600 mg exploratory burden

An earlier exploratory value of 600 mg/day NH3 was rejected as unsuitable for a conservative structural interaction test because its molar loading overwhelmingly dominated the famotidine state. It was not used in the retained dose-series conclusion. The captured series therefore begins at 0.1 mg/day and extends through 5 mg/day, with a 0 mg famotidine-only baseline.

## Structural-family extraction

The 17-row family is a reporting/extraction layer after the 5,734-state calculation. It does not restrict engine execution. Every dose was evaluated against all 5,734 rows before the language/speech cohort was extracted.

## Pair rank versus perturbation magnitude

Pair rank is a decoder of correspondence between the current chemical projection and a represented condition state. It does not replace the perturbation metrics. The archive therefore retains both pair ranks and raw structural evidence (`new_breaks`, `restored_relations`, offsets, direction, etc.).
