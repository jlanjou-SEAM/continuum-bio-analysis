import json, re
from pathlib import Path
from .full_sider import build_compound_projection

DOSE_TO_MG = {"mg":1.0,"g":1000.0,"ug":0.001,"mcg":0.001,"μg":0.001,"ng":0.000001}
SEC = {"second":1.0,"minute":60.0,"hour":3600.0,"day":86400.0,"week":604800.0,"month":2629800.0}
FORMULA_RE = re.compile(r"^(?:[A-Z][a-z]?\d*)+$")


def parse_dose(raw):
    m=re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*(mg|g|ug|mcg|μg|ng)\s*", raw, re.I)
    if not m:
        raise ValueError("DOSE_FORMAT_REQUIRED: examples: 2.5 mg, 40 mg, 10 mcg")
    v=float(m.group(1)); unit=m.group(2).lower()
    if v < 0: raise ValueError("DOSE_MUST_BE_NONNEGATIVE")
    return {"dose_raw":raw,"dose_value":v,"dose_unit":unit,"dose_mass_mg":v*DOSE_TO_MG[unit]}


def parse_interval(raw):
    s=raw.strip().lower()
    aliases={
        "once daily":(1.0,"day"),"daily":(1.0,"day"),"once a day":(1.0,"day"),
        "twice daily":(0.5,"day"),"twice a day":(0.5,"day"),
        "once weekly":(1.0,"week"),"weekly":(1.0,"week"),
        "once monthly":(1.0,"month"),"monthly":(1.0,"month"),
    }
    if s in aliases:
        v,u=aliases[s]; return {"interval_raw":raw,"interval_value":v,"interval_unit":u,"interval_seconds":v*SEC[u]}
    m=re.fullmatch(r"(?:every\s+)?([0-9]+(?:\.[0-9]+)?)\s*(second|seconds|minute|minutes|hour|hours|day|days|week|weeks|month|months)",s)
    if not m:
        raise ValueError("INTERVAL_FORMAT_REQUIRED: examples: once daily, every 6 hours, twice daily")
    v=float(m.group(1)); u=m.group(2).rstrip("s")
    if v <= 0: raise ValueError("INTERVAL_MUST_BE_POSITIVE")
    return {"interval_raw":raw,"interval_value":v,"interval_unit":u,"interval_seconds":v*SEC[u]}


def load_compound_registry(root):
    path=Path(root)/"data/compound_registry.json"
    if not path.exists():
        raise RuntimeError("COMPOUND_REGISTRY_REQUIRED")
    data=json.loads(path.read_text())
    if not isinstance(data,dict):
        raise RuntimeError("COMPOUND_REGISTRY_SCHEMA_INVALID")
    for key,rec in data.items():
        if not isinstance(rec,dict) or not rec.get("canonical_name") or not rec.get("formula"):
            raise RuntimeError(f"COMPOUND_REGISTRY_RECORD_INVALID:{key}")
    return data


def resolve_compound(raw, root, lock):
    q=raw.strip()
    if not q:
        raise ValueError("COMPOUND_REQUIRED")
    registry=load_compound_registry(root)
    if FORMULA_RE.fullmatch(q):
        canonical_name=q
        formula=q
        source="direct_formula"
        registry_key=None
    else:
        registry_key=q.lower()
        rec=registry.get(registry_key)
        if not rec:
            raise RuntimeError("COMPOUND_NAME_NOT_IN_LOCAL_REGISTRY: supply an empirical molecular formula or add a name/formula entry to data/compound_registry.json")
        canonical_name=rec["canonical_name"]
        formula=rec["formula"]
        source="local_name_registry"
    projection=build_compound_projection(lock,formula)
    return {
        "compound_query":q,
        "canonical_name":canonical_name,
        "chemical_formula":formula,
        "formula_source":source,
        "registry_key":registry_key,
        "manifold_projection":projection,
    }
