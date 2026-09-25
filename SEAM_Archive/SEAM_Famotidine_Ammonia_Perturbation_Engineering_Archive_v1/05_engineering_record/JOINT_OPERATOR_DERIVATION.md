# Joint Operator Derivation

The locked v3.12 response equation for one chemical is:

```text
R = normalize(B + L(Q-G))
```

For two independently projected chemicals, define:

```text
LΣ = L1 + L2
QΣ = (L1 Q1 + L2 Q2) / LΣ
```

Substitution gives:

```text
B + LΣ(QΣ-G)

= B + (L1+L2) [ (L1Q1+L2Q2)/(L1+L2) - G ]

= B + L1Q1 + L2Q2 - (L1+L2)G

= B + L1(Q1-G) + L2(Q2-G)
```

The locked engine can therefore evaluate a two-chemical state without changing its row-wise response law. The joint projection is a loading-weighted representation of the simultaneous chemical state, and the normal engine normalization occurs only after both perturbation contributions have entered the row state.

This construction does **not** introduce a pharmacological interaction coefficient. Any nonlinear changes in returned offsets or discrete relation transitions arise from the existing normalization, reference geometry, and relation-boundary crossings of the locked engine.
