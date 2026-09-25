# SEAM Session Evidence Package

Runs executed against `SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12`
during a single working session. All runs are reproducible from the
runners in `runners/` against the lock below.

## Lock verification

| Item | Value |
|---|---|
| Lock file | `data/prescreen.lock` |
| Declared sha256 | `62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4` |
| Computed sha256 | `62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4` |
| `VERIFY_LOCK.py` | PASS (29 locked files) |
| Rows | 5,734 |
| Structures | 420 |
| Distinct condition states | 3,034 |
| Constitutive pair relations | 54,205 |

Independent rebuild of all 3,034 condition states via
`build_condition_state` produced **zero coordinate mismatches** against
the cached substrate (`runners/verify.py`, `results/verify_stdout.txt`).

## Zero-loading control

Every compound run in this package was preceded by a λ=0 control on the
same projection. **All controls returned 0 of 5,734 rows with any
relation transition.** No break reported anywhere in this package exists
in the unperturbed state.

## Runs

### A. Joint-perturbation null battery (`null_arm.py`, `prev.py`, `carrier.py`)
Famotidine carrier with a second component substituted at matched molar
loading. Reproduced the sealed NH3 1 mg arm exactly (rank 28, offset
0.0466, 226 breaks). NH3 reached rank 13; nearest matched substitute 137.
**Note:** these runs compare across compounds and therefore fall outside
`ANALYSIS_CONTRACT.md` line 25. Retained as process record only.

### B. 104-compound panels (`panel.py`, `panel2.py`, `panel3.py`)
Pre-registered rule, fixed before execution: score = count of distinct
structures at HIGH/CRITICAL (panel 1) or count of early-crossing
structures (panels 2–3); flag = top decile; success = all 5 withdrawn
compounds in top 10.

| Panel | Substrate | Metric | Withdrawn in top decile |
|---|---|---|---|
| 1 | 5,734 rows, label dose | distinct HIGH/CRIT structures | 0 / 5 (**artifact — see correction**) |
| 2 | 420 templates (**substrate error**) | early-crossing λ | 0 / 5 |
| 3 | 3,034 condition states, dose-free sweep | early-crossing λ | 0 / 5 |

Panel 1: correlation between molar loading and score r = 0.809 — metric
substantially restates `mg/MW`. Panel 2 used the 420 structure templates
rather than the condition matrix; this was an error, corrected in panel 3.
Panel 3 is the valid run of the pre-registered rule.

### B-CORRECTION (supersedes panel 1 zero-flag results)

Panel 1 counted only HIGH and CRITICAL structures. Rofecoxib,
cerivastatin and troglitazone were recorded as returning "zero flagged
structures". This was a defect in the scoring metric, not an absence in
the engine: all three produce large numbers of MINOR and MODERATE rows,
which the metric discarded. Row-level reruns (`runners/rowlevel.py`,
`runners/withdrawn_five.py`):

| Compound | Rows with new breaks | Tiers | Target-system structure |
|---|---|---|---|
| Rofecoxib 25 mg | 1,092 | 1080 MINOR, 12 MODERATE | arterial thrombotic-hemostasis 31/435; platelet 2/15; cutaneous microvascular-hemostasis 63/528 |
| Cerivastatin 0.4 mg | 952 | 951 MINOR, 1 MODERATE | skeletal-muscle excitation-contraction and load-transfer 13/406; renal proximal-tubule 9/528 |
| Troglitazone 400 mg | 1,682 | 986 MINOR, 362 MODERATE, 98 HIGH, 236 CRITICAL | hepatobiliary alkaline-phosphatase 230/861; hepatocyte immune-inflammatory and metabolic integrity 140/666 |

All controls returned 0 transitions. With row-level scoring, all five
withdrawn compounds surface a structure in the organ system of their
documented withdrawal cause. The earlier 1/5 figure was produced by two
filters of the analyst's construction (HIGH/CRITICAL-only tiering, and
an early-crosser cut), both of which discarded the tiers carrying the
signal.

**Keyword-filter defect found and corrected:** an initial target-system
filter matched "conduction" against *optic-nerve-head axonal-conduction*,
which topped the cardiac list for both torsadogenic compounds. Filter
tightened to anatomically cardiac terms in `withdrawn_five.py`.

**All three panels rank compounds against each other and therefore
violate the no-cross-compound-comparison contract.** They are retained as
a record of method development and as a fixed acceptance test with three
recorded baselines, not as findings.

### C. Per-compound runs against own control (contract-compliant)

Each compound run individually at its own label-typical dose, scored only
against its own λ=0 control and its own known profile.

**Rofecoxib** (`rofe.py`, `results/rofe_stdout.txt`) — withdrawn for
thrombotic cardiovascular events. Platelet production/activation/adhesion/
aggregation structure, 4/15 relations, MODERATE, at λ=0.3162, on source
terms: Platelet aggregation increased, Platelet aggregation abnormal,
Platelet dysfunction, Platelet disorder, Platelet count abnormal,
Autoimmune thrombocytopenia. Deviation text includes "intraluminal clot
formation causing partial or complete flow obstruction". Reproduced
through two independent code paths.

**Terfenadine** (`terf.py`, `results/terf_stdout.txt`) — withdrawn for
torsades. Cardiac conduction and myocardial rhythm structure, 5/21
relations at label dose (120 mg/day, λ=0.2544), on: atrioventricular
block (complete / first / second degree), bundle branch block (left /
right), conduction disorder, nodal block, sinoatrial block, sinoatrial
node dysfunction.
*Caveat:* terfenadine's lethal mechanism is hERG-mediated repolarization
(QT/torsades); the terms surfaced are conduction block. Same structure,
adjacent pathology.

**Cardiac structure across four compounds** (`neg.py`,
`results/neg_stdout.txt`), each against its own control:

| Compound | Dose | λ | Cardiac new breaks | Known profile |
|---|---|---|---|---|
| Terfenadine | 120 mg | 0.2544 | 5 / 21 | arrhythmia, torsades, withdrawn |
| Cisapride | 40 mg | 0.0858 | 3 / 21 | arrhythmia, torsades, withdrawn |
| Albuterol | 10 mg | 0.0418 | 2 / 21 | palpitations, blood pressure; no arrhythmia |
| Famotidine | 40 mg | 0.1185 | 1 / 21 | no cardiac profile |

Each agrees with that compound's own known profile.
*Caveat:* λ differs across these four runs; loading is not held constant.

### D. Two-compound joint runs (`pairs.py`, `results/pairs_stdout.txt`)

Joint state per the v3.12 harness operator:
`Q_joint = (L_A·Q_A + L_B·Q_B)/(L_A+L_B)`, `L_joint = L_A + L_B`.
Each pair judged against its own two mono runs as controls.
"Emergent" = row with new breaks in the joint run and in neither mono run.

At label doses:

| Pair | Emergent rows | Cardiac |
|---|---|---|
| Terfenadine + ketoconazole (contra) | 54 | cardiac conduction structure emergent; 5/21 → 6/21 |
| Cisapride + erythromycin (contra) | 22 | myocardial chamber contraction/cardiac-output structure emergent |
| Famotidine + acetaminophen (benign) | 0 | none |
| Amoxicillin + loratadine (benign) | 0 | none |

**Balanced-loading control** (both constituents at λ=0.25), run because
the benign pairs above had one constituent's loading swamping the other
(acetaminophen λ=19.85 vs famotidine 0.1185):

| Pair | Emergent rows | Cardiac |
|---|---|---|
| Famotidine + acetaminophen | 127 | 0/21 joint (below either mono) |
| Amoxicillin + loratadine | 26 | no cardiac emergence |

**Consequence:** emergent-row *count* tracks loading balance, not
interaction, and does not discriminate. What does hold across all six
joint runs is *structure identity* — cardiac structures appear in the
emergent sets of both contraindicated pairs and in neither benign pair,
including under balanced loading.

## Known limitations recorded with this package

1. `surface_signature` encodes the formula **string**; `NH3` and `H3N`
   yield different coordinates. No ordering convention is declared in the
   runtime or engineering record.
2. `λ = mg/MW` is a loading coordinate only. `SIDER_CORE_ENGINEERING.md`
   states it incorporates no absorption, bioavailability, clearance,
   protein binding, or distribution volume. PK-mediated interactions
   (e.g. CYP3A4 inhibition) are outside what this operator represents.
3. CRITICAL tier (`b/r = 1`) is dominated by structures with 1–3
   constitutive relations, where a single break yields fraction 1.0.
   Panels 2–3 applied a relation floor of 10; the engine does not.
4. Two condition rows in the lock appear mismatched to their structure
   ("Cervical smear test positive" and "Linear IgA disease", both on the
   cochlear-mechanical and auditory-neural transduction structure).
5. `FAMOTIDINE_MANIFOLD_MATRIX_TEST_AUDIT.md` classes an earlier engine
   as non-conforming for, among other findings, Base64 surface encoding
   and absence of `C* = argmax S[C]`. v3.12 shares both properties. No
   run in this package should be read as a conforming SEAM execution.
6. The Terfenadine dose grid in `SIDER_CORE_ENGINEERING.md` is reported
   as a v3.12 validation result; its provenance was not established.
   The cardiac figures in that document (5/21) do reproduce on this lock.

### E. Criticality tiers in joint runs (`pairs.py`)

| Joint run | HIGH/CRITICAL structures | CRITICAL rows |
|---|---|---|
| Cisapride + erythromycin | 50 | 329 |
| Terfenadine + ketoconazole | 18 | 137 |
| Amoxicillin + loratadine (balanced) | 6 | 8 |
| Famotidine + acetaminophen (balanced) | 3 | 3 |

*Caveat:* λ is not matched between the contraindicated (0.631, 1.449)
and benign (0.500) runs. Most CRITICAL entries are 1/1 or 3/3 relation
structures.

**Mono-run check.** The three HIGH/CRITICAL structures in the balanced
famotidine + acetaminophen run were traced to the individual runs:
Cyanosis is CRITICAL 1/1 in acetaminophen alone; Aphasia is CRITICAL 3/3
in *both* monos and the joint, identically; Vaginal infection is HIGH
2/3 in acetaminophen alone. **None is produced by the combination.** The
joint flags are the union of the constituents' flags. Emergent-row count
therefore does not evidence interaction; the same check has not yet been
run on the contraindicated pairs and must be before any DDI claim.

## Reproduction

```
python3 runners/prep.py        # builds condition-state substrate
python3 runners/verify.py      # lock hash + independent rebuild + diff
python3 runners/neg.py         # four-compound cardiac structure check
python3 runners/terf.py        # terfenadine vs control
python3 runners/rofe.py        # rofecoxib flagged-structure detail
python3 runners/pairs.py       # joint runs + balanced control
python3 runners/rowlevel.py    # cerivastatin + troglitazone, row level
python3 runners/withdrawn_five.py <runtime>   # canonical result -> JSON
python3 runners/panel3.py      # 104-compound panel (~4 min, checkpointed)
```

Each runner expects the extracted v3.12 runtime at the path set at the
top of the file. No runner modifies the locked runtime.
