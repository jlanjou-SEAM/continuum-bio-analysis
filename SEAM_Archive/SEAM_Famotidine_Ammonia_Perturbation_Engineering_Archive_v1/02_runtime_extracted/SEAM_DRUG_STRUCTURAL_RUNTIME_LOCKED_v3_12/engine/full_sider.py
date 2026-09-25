"""Pure-Python replay of the locked SIDER_Prescreen_C constitutive engine.

The binary cache and equations are unchanged. This module exists so the three-input
wrapper is portable and can apply the declared dose+interval analysis coordinate
without making compound identity depend on dose or interval.
"""
import math, struct, hashlib
from pathlib import Path

DIMS=128
EPS=1e-15
MAGIC=b"SPCLOS1"
ELEMENT_WEIGHTS={
    "H":1.00794,"He":4.002602,"Li":6.941,"Be":9.012182,"B":10.811,"C":12.0107,"N":14.0067,"O":15.9994,"F":18.9984032,"Ne":20.1797,
    "Na":22.98976928,"Mg":24.3050,"Al":26.9815386,"Si":28.0855,"P":30.973762,"S":32.065,"Cl":35.453,"Ar":39.948,"K":39.0983,"Ca":40.078,
    "Sc":44.955912,"Ti":47.867,"V":50.9415,"Cr":51.9961,"Mn":54.938045,"Fe":55.845,"Co":58.933195,"Ni":58.6934,"Cu":63.546,"Zn":65.38,
    "Ga":69.723,"Ge":72.64,"As":74.92160,"Se":78.96,"Br":79.904,"Kr":83.798,"Rb":85.4678,"Sr":87.62,"Ag":107.8682,"Cd":112.411,
    "Sn":118.710,"Sb":121.760,"Te":127.60,"I":126.90447,"Ba":137.327,"Pt":195.084,"Au":196.966569,"Hg":200.59,"Pb":207.2,
}


def molecular_weight(formula):
    i=0; mw=0.0; atoms=0; counts={}
    while i<len(formula):
        if not formula[i].isupper(): raise ValueError(f"FORMULA_PARSE_FAILED_AT:{i}")
        sym=formula[i]; i+=1
        if i<len(formula) and formula[i].islower(): sym+=formula[i]; i+=1
        j=i
        while j<len(formula) and formula[j].isdigit(): j+=1
        count=int(formula[i:j] or "1"); i=j
        if sym not in ELEMENT_WEIGHTS: raise ValueError(f"ATOMIC_MASS_NOT_BUNDLED:{sym}")
        mw += ELEMENT_WEIGHTS[sym]*count; atoms += count; counts[sym]=counts.get(sym,0)+count
    if atoms<=0: raise ValueError("EMPTY_FORMULA")
    return mw, counts, atoms


def surface_signature(text):
    payload=text.encode("utf-8")
    seq=[]; i=0; n=len(payload)
    while i+3<=n:
        v=(payload[i]<<16)|(payload[i+1]<<8)|payload[i+2]
        seq += [(v>>18)&63,(v>>12)&63,(v>>6)&63,v&63]; i+=3
    rem=n-i
    if rem==1:
        v=payload[i]<<16; seq += [(v>>18)&63,(v>>12)&63]
    elif rem==2:
        v=(payload[i]<<16)|(payload[i+1]<<8); seq += [(v>>18)&63,(v>>12)&63,(v>>6)&63]
    comp=[0.0]*64; rel=[0.0]*64
    for x in seq: comp[x]+=1.0
    if seq: comp=[x/len(seq) for x in comp]
    if len(seq)>1:
        for a,b in zip(seq,seq[1:]): rel[abs(b-a)]+=1.0
        rel=[x/(len(seq)-1) for x in rel]
    out=comp+rel; s=sum(out)
    return [x/s for x in out] if s else out


def _cstring(pool, off):
    end=pool.find(b"\0",off)
    if end<0: end=len(pool)
    return pool[off:end].decode("utf-8")


def load_lock(path):
    data=Path(path).read_bytes(); off=0
    magic,version,dims,manifold_count,structure_count,row_count,pair_count,pool_size=struct.unpack_from("<8s7I",data,off); off+=36
    if magic[:7]!=MAGIC or version!=1 or dims!=DIMS or structure_count!=420 or row_count!=5734:
        raise RuntimeError("UNEXPECTED_SIDER_LOCK_HEADER")
    G=list(struct.unpack_from("<128d",data,off)); off+=8*DIMS
    S=[]
    for _ in range(manifold_count):
        S.append(list(struct.unpack_from("<128d",data,off))); off+=8*DIMS
    structures=[]
    for _ in range(structure_count):
        name_off,pair_off,pair_cnt,needed_count,base_top=struct.unpack_from("<4Ii",data,off); off+=20
        T=list(struct.unpack_from("<128d",data,off)); off+=8*DIMS
        structures.append({"name_off":name_off,"pair_off":pair_off,"pair_count":pair_cnt,"needed_count":needed_count,"base_top":base_top,"T":T})
    pairs=[]
    for _ in range(pair_count):
        a,b,rel,_pad=struct.unpack_from("<BBbB",data,off); off+=4; pairs.append((a,b,rel))
    rows=[]
    for _ in range(row_count):
        bid,sidx,_reserved,dev_off,term_off,part_off=struct.unpack_from("<8sHHIII",data,off); off+=24
        rows.append({"baseline_id":bid.split(b"\0",1)[0].decode("ascii"),"structure_idx":sidx,"deviation_off":dev_off,"term_off":term_off,"partition_off":part_off})
    pool=data[off:off+pool_size]
    for s in structures: s["name"]=_cstring(pool,s["name_off"])
    for r in rows:
        r["structural_deviation"]=_cstring(pool,r["deviation_off"])
        r["source_term"]=_cstring(pool,r["term_off"])
        r["source_partition"]=_cstring(pool,r["partition_off"])
    return {"version":version,"dims":dims,"manifold_count":manifold_count,"structure_count":structure_count,"row_count":row_count,"pair_count":pair_count,"G":G,"S":S,"structures":structures,"pairs":pairs,"rows":rows,"sha256":hashlib.sha256(data).hexdigest()}


def _relation(a,b):
    if abs(a-b)<=1e-12: return 0
    return -1 if a<b else 1


def _js_similarity(A,B):
    A=[max(float(x),EPS) for x in A]; sa=sum(A); A=[x/sa for x in A]
    B=[max(float(x),EPS) for x in B]; sb=sum(B); B=[x/sb for x in B]
    kla=klb=0.0; log2=math.log(2.0)
    for a,b in zip(A,B):
        m=(a+b)*0.5
        kla += a*(math.log(a/m)/log2)
        klb += b*(math.log(b/m)/log2)
    sim=1.0-0.5*(kla+klb)
    return max(0.0,min(1.0,sim))


def _js_argmax(C,S):
    best=-1.0; besti=0
    for i,srow in enumerate(S):
        sim=_js_similarity(C,srow)
        if sim>best: best=sim; besti=i
    return besti


def build_compound_projection(lock, formula):
    """Resolve an empirical formula into the locked 128-coordinate Manifold basis.

    The empirical formula is encoded once, without a shared textual prefix. The
    resulting 128-coordinate state is then explicitly localized against all 232
    retained Manifold surfaces. Downstream execution receives these coordinates,
    never the raw formula string.
    """
    coordinates=surface_signature(formula)
    if len(coordinates)!=lock["dims"]:
        raise RuntimeError("COMPOUND_PROJECTION_DIMENSION_MISMATCH")
    scored=[(i,_js_similarity(coordinates,s)) for i,s in enumerate(lock["S"])]
    scored.sort(key=lambda x:(-x[1],x[0]))
    coord_hash=hashlib.sha256(
        (formula+"|"+",".join(f"{x:.17g}" for x in coordinates)).encode()
    ).hexdigest()
    return {
        "formula":formula,
        "coordinate_basis":"SIDER_PRESCREEN_C_LOCK/1:128D",
        "coordinate_source":"empirical_formula_surface_signature_without_shared_prefix",
        "coordinates":coordinates,
        "coordinate_sha256":coord_hash,
        "manifold_lookup_count":lock["manifold_count"],
        "manifold_top_entry_index":scored[0][0],
        "manifold_top_similarity":scored[0][1],
        "manifold_top_entries":[{"index":i,"similarity":sim} for i,sim in scored[:5]],
    }


def resolve_structure(lock,s,Q,loading_mmol):
    raw=[max(t+loading_mmol*(q-g),EPS) for t,q,g in zip(s["T"],Q,lock["G"])]
    total=sum(raw); C=[x/total for x in raw]
    broken=0
    for a,b,rel in lock["pairs"][s["pair_off"]:s["pair_off"]+s["pair_count"]]:
        if _relation(C[a],C[b])!=rel: broken+=1
    relation_count=s["pair_count"]
    frac=(broken/relation_count) if relation_count else 0.0
    closure=(frac*math.log1p(relation_count)) if broken and relation_count else 0.0
    if not broken: tier,tier_order="NONE",0
    elif frac<=0.25: tier,tier_order="LOW",1
    elif frac<=0.50: tier,tier_order="MEDIUM",2
    elif frac<1.0: tier,tier_order="HIGH",3
    else: tier,tier_order="CRITICAL",4
    return {
        "necessary_coordinate_count":s["needed_count"],"constitutive_relation_count":relation_count,
        "constitutive_relations_broken":broken,"closure_broken":bool(broken),
        "baseline_top_entry_index":s["base_top"],"compound_top_entry_index":_js_argmax(C,lock["S"]),
        "break_fraction":frac,"closure_load":closure,"tier":tier,"tier_order":tier_order,
    }


def effect_score(metric, manifold_count):
    """Generic ranking: closure magnitude with bounded support/localization modifiers.

    Closure remains dominant. Support contributes at most +50%; localization movement
    contributes at most +10%. No compound identity, clinical indication, or effect label enters.
    """
    support=math.log1p(metric["necessary_coordinate_count"])/math.log(129.0)
    shift=abs(metric["compound_top_entry_index"]-metric["baseline_top_entry_index"])/max(manifold_count-1,1)
    return metric["closure_load"]*(1.0+0.5*support)*(1.0+0.1*shift)


def run_full(lock, compound_projection, loading_mmol):
    if not isinstance(compound_projection,dict):
        raise TypeError("COMPOUND_MANIFOLD_PROJECTION_REQUIRED")
    Q=compound_projection.get("coordinates")
    if not isinstance(Q,list) or len(Q)!=lock["dims"]:
        raise RuntimeError("COMPOUND_MANIFOLD_COORDINATES_REQUIRED")
    Q=[float(x) for x in Q]
    structure_results=[]
    for s in lock["structures"]:
        m=resolve_structure(lock,s,Q,loading_mmol)
        m["structure"]=s["name"]
        m["localization_identity_preserved"]=(m["compound_top_entry_index"]==m["baseline_top_entry_index"])
        m["effect_score"]=effect_score(m,lock["manifold_count"])
        structure_results.append(m)
    row_results=[]
    tier_counts={"NONE":0,"LOW":0,"MEDIUM":0,"HIGH":0,"CRITICAL":0}
    for r in lock["rows"]:
        m=structure_results[r["structure_idx"]]
        tier_counts[m["tier"]]+=1
        row_results.append({
            "baseline_id":r["baseline_id"],"structure":m["structure"],"structural_deviation":r["structural_deviation"],
            "source_term":r["source_term"],"source_partition":r["source_partition"],**m,
        })
    return {"structure_results":structure_results,"row_results":row_results,"tier_counts":tier_counts,"Q":Q}
