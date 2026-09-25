# Captured Results

Famotidine was held fixed at 40 mg once daily.

| NH3 retained burden (mg/day) | Mean abs. language-family offset | Change vs famotidine | New breaks | Restored | Best language pair rank |
|---:|---:|---:|---:|---:|---:|
| 0 | 0.0185128139 | 0.0% | 151 | 64 | 182 |
| 0.1 | 0.0198914872 | +7.45% | 160 | 64 | 75 |
| 0.25 | 0.0220652678 | +19.19% | 167 | 63 | 52 |
| 0.5 | 0.0263401707 | +42.28% | 185 | 63 | 35 |
| 1 | 0.0364889378 | +97.10% | 226 | 63 | 28 |
| 2 | 0.0606800840 | +227.77% | 259 | 74 | 27 |
| 5 | 0.1468991860 | +693.50% | 364 | 111 | 13 |

## Word-finding row

`SB5705 — Word finding difficulty` increased in absolute structural offset from:

```text
0 mg NH3:  0.0244017652
0.1 mg:    0.0266203369
0.25 mg:   0.0296460392
0.5 mg:    0.0350736892
1 mg:      0.0466495302
2 mg:      0.0710365422
5 mg:      0.1548099188
```

Its pair rank moved from `182` at famotidine alone to `13` at the 5 mg/day NH3 retained-burden coordinate.

## 1 mg control comparison

For the frozen 17-row language/speech family:

```text
Famotidine 40 mg/day alone: mean abs offset = 0.0185128139
NH3 1 mg/day alone:         mean abs offset = 0.0160160455
Joint state:                mean abs offset = 0.0364889378
```

The control runs are preserved under `04_results/controls/` and the joint-state ledger under `04_results/reproduced_dose_series/nh3_1p0mg_day/`.

## Cause-and-effect statement represented by this archive

Within the locked v3.12 perturbation model, adding the declared NH3 chemical burden to the famotidine state causes a larger displacement of the same represented language/CNS structural family than famotidine alone, and the displacement increases across the tested NH3 burden series.
