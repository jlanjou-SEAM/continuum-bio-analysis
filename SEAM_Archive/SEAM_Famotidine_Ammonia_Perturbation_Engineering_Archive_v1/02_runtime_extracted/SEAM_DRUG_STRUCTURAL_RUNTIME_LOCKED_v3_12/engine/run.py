import csv, hashlib, json, time
from pathlib import Path
from .inputs import resolve_compound, parse_dose, parse_interval
from .full_sider import load_lock, molecular_weight
from .rowwise import run_condition_matrix
from .pairwise import resolve_pair_matrix

ROOT=Path(__file__).resolve().parents[1]


def _slug(s):
    return "".join(ch if ch.isalnum() else "_" for ch in str(s)).strip("_")


def _formula_hash(formula,Q):
    return hashlib.sha256((formula+"|"+",".join(f"{x:.17g}" for x in Q)).encode()).hexdigest()


def _write_csv(path, rows, rank_field=None):
    fields=[
        "baseline_id","source_term","structure","structural_deviation","source_partition",
        "condition_state_sha256","constitutive_relation_count","initial_broken_relations",
        "restored_relations","new_breaks","residual_broken_relations","relation_transition_count",
        "initial_offset","residual_offset","net_offset_change","absolute_offset_change","direction",
        "new_break_fraction","criticality","criticality_order","reference_baseline_top_entry_index",
        "condition_top_entry_index","response_top_entry_index","response_state_sha256",
        "pair_correspondence","pair_js_correspondence","pair_sign_continuity","relation_balance",
        "pair_active_hit","pair_rank_within_active_hits"
    ]
    with Path(path).open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow(dict(r))


def run(compound_raw, dose_raw, interval_raw, output_dir=None, make_pdf=True):
    t0=time.perf_counter()
    lock=load_lock(ROOT/"data/prescreen.lock")
    compound=resolve_compound(compound_raw,ROOT,lock)
    dose=parse_dose(dose_raw); interval=parse_interval(interval_raw)
    formula=compound["chemical_formula"]
    mw,counts,atom_count=molecular_weight(formula)
    daily_factor=86400.0/interval["interval_seconds"]
    daily_equivalent_mg=dose["dose_mass_mg"]*daily_factor
    loading_mmol_per_day=daily_equivalent_mg/mw

    rowwise=run_condition_matrix(lock,compound["manifold_projection"],loading_mmol_per_day)
    paired=resolve_pair_matrix(lock,compound["manifold_projection"],rowwise["rows"])
    Q=compound["manifold_projection"]["coordinates"]
    compound["molecular_mass_g_mol"]=mw
    compound["elemental_composition"]=counts
    compound["atom_count"]=atom_count
    compound["compound_structure_sha256"]=_formula_hash(formula,Q)
    compound["compound_projection_sha256"]=compound["manifold_projection"]["coordinate_sha256"]

    pair_ranked=paired["pair_ranked_active_hits"]
    primary=[dict(pair_ranked[0],effect_role="PRIMARY EFFECT")] if pair_ranked else []
    secondary=[dict(r,effect_role="SECONDARY EFFECT") for r in pair_ranked[1:12]]
    selected={r["baseline_id"] for r in primary+secondary}
    severe=[dict(r,effect_role="HIGH / CRITICAL STRUCTURAL BREACH") for r in pair_ranked
            if r["baseline_id"] not in selected and r["criticality"] in {"HIGH","CRITICAL"}]

    token=(f"{formula}|{dose['dose_mass_mg']:.17g}|{interval['interval_seconds']:.17g}|"
           f"{lock['sha256']}|ROWWISE_5734_PAIRWISE_V2")
    run_id="RUN_"+hashlib.sha256(token.encode()).hexdigest()[:16].upper()
    out=Path(output_dir or ROOT/"runtime/output")
    out.mkdir(parents=True,exist_ok=True)
    process=out/"process"; process.mkdir(parents=True,exist_ok=True)
    (process/"01_compound_resolution.json").write_text(json.dumps({k:v for k,v in compound.items() if k!="manifold_projection"},indent=2,sort_keys=True)+"\n")
    (process/"02_compound_manifold_projection.json").write_text(json.dumps(compound["manifold_projection"],indent=2,sort_keys=True)+"\n")
    (process/"03_exposure_resolution.json").write_text(json.dumps({
        "dose":dose,"interval":interval,"daily_equivalent_analysis_mg":daily_equivalent_mg,
        "compound_loading_mmol_per_day":loading_mmol_per_day
    },indent=2,sort_keys=True)+"\n")

    row_payload=json.dumps(rowwise["rows"],sort_keys=True,separators=(",",":"))
    rowwise_sha256=hashlib.sha256(row_payload.encode()).hexdigest()
    (process/"04_rowwise_condition_comparison.json").write_text(json.dumps({
        "evaluation_mode":"ROWWISE_CONDITION_STATE_PERTURBATION",
        "compound_projection_sha256":compound["compound_projection_sha256"],
        "rowwise_comparison_sha256":rowwise_sha256,
        "condition_rows":len(rowwise["rows"]),
        "parent_constitutive_templates":lock["structure_count"],
        "unique_condition_state_hashes":rowwise["counts"]["unique_condition_state_hashes"],
        "rows":rowwise["rows"]
    },indent=2,sort_keys=True)+"\n")

    pair_process_rows=[{
        "baseline_id":r["baseline_id"],"pair_active_hit":r["pair_active_hit"],
        "pair_rank_within_active_hits":r["pair_rank_within_active_hits"],
        "pair_correspondence":r["pair_correspondence"],
        "pair_js_correspondence":r["pair_js_correspondence"],
        "pair_sign_continuity":r["pair_sign_continuity"],
        "relation_transition_count":r["relation_transition_count"],
        "restored_relations":r["restored_relations"],"new_breaks":r["new_breaks"],
        "direction":r["direction"],"absolute_offset_change":r["absolute_offset_change"],
    } for r in paired["rows"]]
    (process/"05_pair_resolution.json").write_text(json.dumps({
        "evaluation_mode":"PAIR_RESOLUTION_ON_CURRENT_COMPOUND_AND_EACH_CONDITION_STATE",
        "compound_projection_sha256":compound["compound_projection_sha256"],
        "rowwise_comparison_sha256":rowwise_sha256,
        "pair_resolution_sha256":paired["pair_resolution_sha256"],
        "condition_rows":len(paired["rows"]),
        "active_hit_count":len(pair_ranked),
        "operator":paired["operator"],
        "rows":pair_process_rows,
    },indent=2,sort_keys=True)+"\n")

    raw=out/"full_sider_raw"; raw.mkdir(parents=True,exist_ok=True)
    _write_csv(raw/"results_all_5734.csv",paired["rows"])
    _write_csv(raw/"pair_ranked_active_hits.csv",pair_ranked)

    counts=dict(rowwise["counts"]); counts.update(paired["counts"])
    result={
        "complete":True,"run_id":run_id,"contract":"SEAM_DRUG_STRUCTURAL_RUNTIME/3.12.0-ROWWISE-PAIR-RESOLVED",
        "compound_query":compound_raw,"canonical_name":compound["canonical_name"],"chemical_formula":formula,
        "input":{"compound":compound_raw,"dose":dose_raw,"interval":interval_raw,"normalized_compound":compound,"normalized_dose":dose,"normalized_interval":interval},
        "exposure":{"daily_equivalent_analysis_mg":daily_equivalent_mg,"compound_loading_mmol_per_day":loading_mmol_per_day,"compound_loading_mol_per_day":loading_mmol_per_day/1000.0,"interval_seconds":interval["interval_seconds"]},
        "matrix":{"condition_rows":lock["row_count"],"parent_constitutive_templates":lock["structure_count"],"constitutive_pairs":lock["pair_count"],"manifold_entries":lock["manifold_count"],"lock_sha256":lock["sha256"],"rowwise_comparison_sha256":rowwise_sha256,"pair_resolution_sha256":paired["pair_resolution_sha256"],"evaluation_mode":"ROWWISE_5734_PLUS_PAIR_RESOLUTION"},
        "compound_manifold_projection":{k:v for k,v in compound["manifold_projection"].items() if k!="coordinates"},
        "counts":counts,
        "pair_resolution_contract":paired["operator"],
        "ranking_contract":{
            "scope":"within this compound run only",
            "eligibility":"relation_transition_count > 0; pair correspondence cannot create a hit",
            "primary_order":"pair correspondence descending among active hits",
            "tie_break":"baseline_id ascending",
            "perturbation_metrics":"restored/new/residual relations, offset direction and criticality remain independent evidence and are not multiplied into pair score",
            "cross_compound_comparison":False,
        },
        "primary_effects":primary,"secondary_effects":secondary,"high_critical_breaches":severe,
        "all_rows":paired["rows"],
        "runtime_seconds":time.perf_counter()-t0,
        "analysis_notice":"Structural analysis output only. Each of 5,734 condition/deviation states is perturbed independently by the current compound, then pair-resolved against that same compound state. Pair correspondence does not create a hit and no other compound participates in ranking or resolution."
    }
    result_path=out/"result.json"; result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    if make_pdf:
        from report.write_pdf import build_pdf
        pdf_path=out/f"{_slug(compound['canonical_name'])}_{_slug(dose_raw)}_{_slug(interval_raw)}_Continuum_Bio_Compound_Decoder.pdf"
        build_pdf(result_path,pdf_path); result["report_path"]=str(pdf_path); result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    return result
