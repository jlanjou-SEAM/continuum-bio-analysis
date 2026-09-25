"""Row-wise compound perturbation across the full 5,734-condition matrix.

Each condition/deviation row is constructed and perturbed independently. The
420 locked structure records are retained only as constitutive reference
templates for the row's named biological structure; their result is never
expanded or copied across rows.
"""
import hashlib, math
from .full_sider import EPS, surface_signature, _js_similarity, _js_argmax


def _relation(a,b):
    if abs(a-b) <= 1e-12:
        return 0
    return -1 if a < b else 1


def _state_sha256(label, values):
    payload = label + "|" + ",".join(f"{float(x):.17g}" for x in values)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_condition_state(lock, row):
    """Construct the row's represented biological condition state.

    Only the row's structural representation enters: structure + structural
    deviation. source_term is a reporting/provenance label and is deliberately
    excluded so aliases do not create different physics.
    """
    structure = lock["structures"][row["structure_idx"]]
    representation = structure["name"] + "\n" + row["structural_deviation"]
    coordinates = surface_signature(representation)
    if len(coordinates) != lock["dims"]:
        raise RuntimeError("CONDITION_STATE_DIMENSION_MISMATCH")
    return {
        "representation": representation,
        "coordinates": coordinates,
        "state_sha256": _state_sha256(representation, coordinates),
    }


def _normalize_loaded(base, Q, G, loading):
    raw = [max(float(b) + loading*(float(q)-float(g)), EPS) for b,q,g in zip(base,Q,G)]
    total = sum(raw)
    if total <= 0:
        raise RuntimeError("NONPOSITIVE_RESPONSE_STATE")
    return [x/total for x in raw]


def _criticality(new_breaks, relation_count):
    if new_breaks <= 0 or relation_count <= 0:
        return "INFORMATIONAL", 0, 0.0
    frac = new_breaks / relation_count
    if frac <= 0.25:
        return "MINOR", 1, frac
    if frac <= 0.50:
        return "MODERATE", 2, frac
    if frac < 1.0:
        return "HIGH", 3, frac
    return "CRITICAL", 4, frac


def resolve_condition_row(lock, row, compound_projection, loading_mmol, include_localization=False):
    Q = compound_projection.get("coordinates") if isinstance(compound_projection,dict) else None
    if not isinstance(Q,list) or len(Q) != lock["dims"]:
        raise RuntimeError("COMPOUND_MANIFOLD_COORDINATES_REQUIRED")

    structure = lock["structures"][row["structure_idx"]]
    condition = build_condition_state(lock,row)
    B = condition["coordinates"]
    R = _normalize_loaded(B,Q,lock["G"],loading_mmol)

    pairs = lock["pairs"][structure["pair_off"]:structure["pair_off"]+structure["pair_count"]]
    initial_broken = set()
    response_broken = set()
    for idx,(a,b,rel) in enumerate(pairs):
        if _relation(B[a],B[b]) != rel:
            initial_broken.add(idx)
        if _relation(R[a],R[b]) != rel:
            response_broken.add(idx)

    restored = len(initial_broken - response_broken)
    new_breaks = len(response_broken - initial_broken)
    relation_transitions = restored + new_breaks
    relation_count = len(pairs)
    initial_offset = 1.0 - _js_similarity(B,structure["T"])
    residual_offset = 1.0 - _js_similarity(R,structure["T"])
    net_offset_change = residual_offset - initial_offset
    if net_offset_change < -1e-15:
        direction = "TOWARD_REFERENCE"
    elif net_offset_change > 1e-15:
        direction = "AWAY_FROM_REFERENCE"
    else:
        direction = "NO_NET_OFFSET_CHANGE"
    criticality, criticality_order, new_break_fraction = _criticality(new_breaks,relation_count)

    rec = {
        "baseline_id": row["baseline_id"],
        "structure": structure["name"],
        "structural_deviation": row["structural_deviation"],
        "source_term": row["source_term"],
        "source_partition": row["source_partition"],
        "condition_state_sha256": condition["state_sha256"],
        "constitutive_relation_count": relation_count,
        "initial_broken_relations": len(initial_broken),
        "restored_relations": restored,
        "new_breaks": new_breaks,
        "residual_broken_relations": len(response_broken),
        "relation_transition_count": relation_transitions,
        "initial_offset": initial_offset,
        "residual_offset": residual_offset,
        "net_offset_change": net_offset_change,
        "absolute_offset_change": abs(net_offset_change),
        "direction": direction,
        "new_break_fraction": new_break_fraction,
        "criticality": criticality,
        "criticality_order": criticality_order,
        "reference_baseline_top_entry_index": structure["base_top"],
        "response_state_sha256": _state_sha256(row["baseline_id"],R),
    }
    if include_localization:
        rec["condition_top_entry_index"] = _js_argmax(B,lock["S"])
        rec["response_top_entry_index"] = _js_argmax(R,lock["S"])
    return rec


def run_condition_matrix(lock, compound_projection, loading_mmol):
    if not isinstance(compound_projection,dict):
        raise TypeError("COMPOUND_MANIFOLD_PROJECTION_REQUIRED")
    Q=compound_projection.get("coordinates")
    if not isinstance(Q,list) or len(Q)!=lock["dims"]:
        raise RuntimeError("COMPOUND_MANIFOLD_COORDINATES_REQUIRED")

    rows=[resolve_condition_row(lock,row,compound_projection,loading_mmol,False) for row in lock["rows"]]

    # Ranking is entirely within this single compound run. No other compound
    # participates. Absolute offset displacement is the primary ordering; the
    # number of constitutive transitions resolves ties without a fitted weight.
    ranked=sorted(rows,key=lambda r:(-r["absolute_offset_change"],-r["relation_transition_count"],r["baseline_id"]))

    # Localize only the report-leading states; this avoids 5,734 x 232 repeated
    # Manifold searches while preserving a complete row-wise calculation.
    row_by_id={r["baseline_id"]:raw for r,raw in zip(rows,lock["rows"])}
    for rec in ranked[:24]:
        detailed=resolve_condition_row(lock,row_by_id[rec["baseline_id"]],compound_projection,loading_mmol,True)
        rec.update({k:v for k,v in detailed.items() if k.endswith("top_entry_index")})

    counts={
        "condition_states_evaluated": len(rows),
        "rows_with_relation_transition": sum(1 for r in rows if r["relation_transition_count"]>0),
        "rows_with_new_breaks": sum(1 for r in rows if r["new_breaks"]>0),
        "rows_with_restoration": sum(1 for r in rows if r["restored_relations"]>0),
        "toward_reference": sum(1 for r in rows if r["direction"]=="TOWARD_REFERENCE"),
        "away_from_reference": sum(1 for r in rows if r["direction"]=="AWAY_FROM_REFERENCE"),
        "no_net_offset_change": sum(1 for r in rows if r["direction"]=="NO_NET_OFFSET_CHANGE"),
    }
    criticality_counts={k:sum(1 for r in rows if r["criticality"]==k) for k in ["INFORMATIONAL","MINOR","MODERATE","HIGH","CRITICAL"]}
    counts["criticality_counts"]=criticality_counts
    counts["unique_condition_state_hashes"]=len({r["condition_state_sha256"] for r in rows})
    return {"rows":rows,"ranked_rows":ranked,"counts":counts}
