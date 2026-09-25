"""Pairwise structural correspondence stage for the v3.12 decoder.

This restores the correspondence operator retained in the earlier v3.7
comparison stage, but applies it to the full v3.11/v3.12 5,734-row condition
matrix. It does not rerun exposure perturbation and it does not create a hit.
A row must already contain a compound-induced constitutive transition before it
can enter primary/secondary pair ranking.
"""
import math, hashlib, json
from .rowwise import build_condition_state

EPS=1e-15


def _normalize(v):
    v=[max(float(x),EPS) for x in v]
    s=sum(v) or 1.0
    return [x/s for x in v]


def js_similarity(p,q):
    """Exact v3.7 correspondence form: 1 - sqrt(Jensen-Shannon divergence)."""
    p=_normalize(p); q=_normalize(q)
    n=min(len(p),len(q)); p=_normalize(p[:n]); q=_normalize(q[:n])
    m=[(a+b)/2.0 for a,b in zip(p,q)]
    def kl(a,b):
        return sum(x*math.log(x/y,2) for x,y in zip(a,b) if x>0 and y>0)
    js=(kl(p,m)+kl(q,m))/2.0
    return max(0.0,1.0-math.sqrt(max(js,0.0)))


def sign_continuity(p,q):
    """Exact v3.7 centered-sign continuity term."""
    n=min(len(p),len(q)); p=p[:n]; q=q[:n]
    ap=sum(p)/n; aq=sum(q)/n
    same=sum(1 for a,b in zip(p,q)
             if (a-ap==0) or (b-aq==0) or (((a-ap)>0)==((b-aq)>0)))
    return same/n


def pair_correspondence(p,q):
    js=js_similarity(p,q)
    sc=sign_continuity(p,q)
    return 0.82*js + 0.18*sc, js, sc


def resolve_pair_matrix(lock, compound_projection, rowwise_rows):
    """Decode pair correspondence for all saved row-wise results.

    `rowwise_rows` already contains the compound-induced structural transition
    metrics. This function only evaluates current compound state Q against each
    independently represented biological condition state B_j.

    Pair correspondence never creates a hit. Primary/secondary eligibility is
    restricted to rows whose saved relation_transition_count > 0.
    """
    if not isinstance(compound_projection,dict):
        raise TypeError("COMPOUND_MANIFOLD_PROJECTION_REQUIRED")
    Q=compound_projection.get("coordinates")
    if not isinstance(Q,list) or len(Q)!=lock["dims"]:
        raise RuntimeError("COMPOUND_MANIFOLD_COORDINATES_REQUIRED")

    raw_by_id={r["baseline_id"]:r for r in lock["rows"]}
    decoded=[]
    for saved in rowwise_rows:
        raw=raw_by_id.get(saved["baseline_id"])
        if raw is None:
            raise RuntimeError(f"PAIR_ROW_NOT_IN_LOCK:{saved['baseline_id']}")
        condition=build_condition_state(lock,raw)
        pc,js,sc=pair_correspondence(Q,condition["coordinates"])
        rec=dict(saved)
        rec["pair_correspondence"]=pc
        rec["pair_js_correspondence"]=js
        rec["pair_sign_continuity"]=sc
        rec["pair_active_hit"]=bool(int(saved["relation_transition_count"])>0)
        rec["relation_balance"]=int(saved["restored_relations"])-int(saved["new_breaks"])
        decoded.append(rec)

    active=[r for r in decoded if r["pair_active_hit"]]
    # This is the exact ranking rule tested in the post-decode recovery: pair
    # correspondence is the primary order. Displacement magnitude remains
    # evidence and is not multiplied into the pair score.
    active.sort(key=lambda r:(-float(r["pair_correspondence"]),r["baseline_id"]))
    for i,r in enumerate(active,1):
        r["pair_rank_within_active_hits"]=i

    by_id={r["baseline_id"]:r for r in active}
    rows=[]
    for rec in decoded:
        if rec["baseline_id"] in by_id:
            rec=by_id[rec["baseline_id"]]
        else:
            rec["pair_rank_within_active_hits"]=None
        rows.append(rec)

    payload=[{
        "baseline_id":r["baseline_id"],
        "pair_correspondence":r["pair_correspondence"],
        "pair_js_correspondence":r["pair_js_correspondence"],
        "pair_sign_continuity":r["pair_sign_continuity"],
        "pair_active_hit":r["pair_active_hit"],
        "pair_rank_within_active_hits":r["pair_rank_within_active_hits"],
    } for r in rows]
    pair_sha256=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
        "rows":rows,
        "pair_ranked_active_hits":active,
        "pair_resolution_sha256":pair_sha256,
        "counts":{
            "pair_rows_evaluated":len(rows),
            "pair_ranked_active_hits":len(active),
            "pair_inactive_rows":len(rows)-len(active),
        },
        "operator":{
            "lineage":"v3.7 compare_surface correspondence stage",
            "formula":"0.82 * JS_similarity(compound_state, condition_state) + 0.18 * sign_continuity(compound_state, condition_state)",
            "hit_gate":"relation_transition_count > 0 from the saved row-wise perturbation",
            "ranking":"descending pair_correspondence among active hits; baseline_id ascending tie-break",
            "cross_compound_comparison":False,
        },
    }
