# Execution Pipeline

```text
LOCKED v3.12 DATA + ENGINE
        |
        +--> verify LOCK.json / locked files
        +--> regression tests
        |
        v
Famotidine name --------------------> registry -> C8H15N7O2S3 -> Q_F (128D)
40 mg once daily -------------------> exposure -> L_F = 0.1185376953 mmol/day

NH3 formula ------------------------> direct formula -> Q_A (128D)
retained burden + once daily -------> exposure -> L_A
        |
        v
JOINT ASSEMBLY OUTSIDE LOCKED ENGINE
        |
        +--> L_joint = L_F + L_A
        +--> Q_joint = (L_F Q_F + L_A Q_A) / L_joint
        |
        v
UNCHANGED v3.12 ROW-WISE ENGINE
        |
        +--> load 5,734 condition/deviation rows
        +--> build independent B_j for every row
        +--> R_j = normalize(B_j + L_joint(Q_joint-G))
        +--> compare B_j and R_j to locked parent constitutive relations
        +--> restored / new breaks / residual / offsets / direction
        |
        v
UNCHANGED v3.12 PAIR RESOLVER
        |
        +--> Q_joint x B_j correspondence
        +--> hit gate: relation_transition_count > 0
        +--> deterministic within-run ranking
        |
        v
FULL 5,734-ROW LEDGER + ACTIVE-HIT LEDGER
        |
        v
FROZEN STRUCTURAL FAMILY EXTRACTION
        |
        +--> 17 language/speech rows
        |
        v
DOSE-SERIES COMPARISON
        |
        +--> 0 / 0.1 / 0.25 / 0.5 / 1 / 2 / 5 mg/day NH3 burden
        +--> displacement, breaks, restorations, pair rank
```

## Separation of responsibilities

### Locked engine
Determines chemical projection, condition-state construction, structural perturbation, constitutive relation changes, offsets, criticality, and pair correspondence.

### Experiment harness
Only performs multi-chemical state composition, repeats the unchanged engine across declared NH3 burden coordinates, freezes/extracts the structural family, and summarizes the returned metrics.

### Interpretation
No clinical interpretation is used to create or rank the structural result. Manufacturer warnings and conventional adverse-event descriptions are downstream comparators and are not engine inputs.
