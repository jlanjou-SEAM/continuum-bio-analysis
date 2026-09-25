#!/usr/bin/env python3
"""Reproduce the famotidine + ammonia joint-perturbation dose series.

This harness does not edit the locked v3.12 runtime. It imports its public engine
functions, constructs one weighted joint 128-coordinate chemical projection, and
passes that joint state to the unchanged row-wise and pairwise operators.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, sys
from pathlib import Path

CSV_FIELDS=[
    "baseline_id","source_term","structure","structural_deviation","source_partition",
    "condition_state_sha256","constitutive_relation_count","initial_broken_relations",
    "restored_relations","new_breaks","residual_broken_relations","relation_transition_count",
    "initial_offset","residual_offset","net_offset_change","absolute_offset_change","direction",
    "new_break_fraction","criticality","criticality_order","reference_baseline_top_entry_index",
    "condition_top_entry_index","response_top_entry_index","response_state_sha256",
    "pair_correspondence","pair_js_correspondence","pair_sign_continuity","relation_balance",
    "pair_active_hit","pair_rank_within_active_hits"
]


def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def write_csv(path: Path, rows, fields=CSV_FIELDS):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader(); w.writerows(rows)


def weighted_joint_projection(qf: dict, qa: dict, lf: float, la: float) -> dict:
    total=lf+la
    if total <= 0: raise ValueError('JOINT_LOADING_MUST_BE_POSITIVE')
    if la == 0:
        coords=[float(x) for x in qf['coordinates']]
    else:
        coords=[(lf*float(a)+la*float(b))/total for a,b in zip(qf['coordinates'],qa['coordinates'])]
    payload=','.join(f'{x:.17g}' for x in coords)
    return {
        'formula':'JOINT:C8H15N7O2S3+NH3',
        'coordinate_basis':qf.get('coordinate_basis'),
        'coordinate_source':'loading_weighted_joint_of_locked_v3_12_compound_projections',
        'coordinates':coords,
        'coordinate_sha256':hashlib.sha256(payload.encode()).hexdigest(),
        'joint_components':[
            {'formula':'C8H15N7O2S3','loading_mmol_per_day':lf},
            {'formula':'NH3','loading_mmol_per_day':la},
        ],
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--runtime', required=True, help='Extracted SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12 directory')
    ap.add_argument('--out', required=True)
    ap.add_argument('--nh3-doses', default='0,0.1,0.25,0.5,1,2,5')
    args=ap.parse_args()
    runtime=Path(args.runtime).resolve(); out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    sys.path.insert(0,str(runtime))
    from engine.full_sider import load_lock, molecular_weight
    from engine.inputs import resolve_compound
    from engine.rowwise import run_condition_matrix
    from engine.pairwise import resolve_pair_matrix

    lock=load_lock(runtime/'data/prescreen.lock')
    fam=resolve_compound('Famotidine',runtime,lock)
    amm=resolve_compound('NH3',runtime,lock)
    fam_mw,_,_=molecular_weight(fam['chemical_formula'])
    amm_mw,_,_=molecular_weight('NH3')
    fam_mg_day=40.0
    lf=fam_mg_day/fam_mw
    doses=[float(x) for x in args.nh3_doses.split(',')]

    all_language=[]; summaries=[]; frozen_ids=None
    for dose in doses:
        la=dose/amm_mw
        qj=weighted_joint_projection(fam['manifold_projection'],amm['manifold_projection'],lf,la)
        lj=lf+la
        rowwise=run_condition_matrix(lock,qj,lj)
        paired=resolve_pair_matrix(lock,qj,rowwise['rows'])
        rows=paired['rows']; active=paired['pair_ranked_active_hits']
        by_id={r['baseline_id']:r for r in rows}
        if frozen_ids is None:
            frozen_ids=sorted(r['baseline_id'] for r in rows if ('language-processing' in r['structure'].lower() or 'speech-planning' in r['structure'].lower()))
            if len(frozen_ids)!=17: raise RuntimeError(f'EXPECTED_17_LANGUAGE_ROWS_GOT_{len(frozen_ids)}')
        family=[dict(by_id[i]) for i in frozen_ids]
        rank={r['baseline_id']:r.get('pair_rank_within_active_hits') for r in active}
        for r in family:
            r['pair_rank_within_active_hits']=rank.get(r['baseline_id'])
            r['nh3_mg_per_day']=dose
            r['nh3_loading_mmol_per_day']=la
            r['joint_loading_mmol_per_day']=lj
        all_language.extend(family)

        dose_slug=str(dose).replace('.','p')
        ddir=out/f'nh3_{dose_slug}mg_day'; ddir.mkdir(exist_ok=True)
        write_csv(ddir/'results_all_5734.csv',rows)
        write_csv(ddir/'pair_ranked_active_hits.csv',active)
        lang_fields=[
            'baseline_id','structure','structural_deviation','source_term','source_partition',
            'condition_state_sha256','constitutive_relation_count','initial_broken_relations',
            'restored_relations','new_breaks','residual_broken_relations','relation_transition_count',
            'initial_offset','residual_offset','net_offset_change','absolute_offset_change','direction',
            'new_break_fraction','criticality','criticality_order','reference_baseline_top_entry_index',
            'response_state_sha256','pair_correspondence','pair_js_correspondence','pair_sign_continuity',
            'pair_active_hit','relation_balance','pair_rank_within_active_hits',
            'condition_top_entry_index','response_top_entry_index'
        ]
        write_csv(ddir/'language_family_17_rows.csv',family,lang_fields)
        (ddir/'joint_state.json').write_text(json.dumps({
            'nh3_mg_per_day':dose,
            'famotidine_mg_per_day':fam_mg_day,
            'famotidine_loading_mmol_per_day':lf,
            'nh3_loading_mmol_per_day':la,
            'joint_loading_mmol_per_day':lj,
            'joint_projection':qj,
            'rowwise_counts':rowwise['counts'],
            'pair_counts':paired['counts'],
            'pair_operator':paired['operator'],
        },indent=2,sort_keys=True)+'\n')

        wf=next(r for r in family if r['source_term']=='Word finding difficulty')
        active_family=[r for r in family if r['relation_transition_count']>0]
        vals=[r['absolute_offset_change'] for r in family]
        summary={
            'nh3_mg_per_day':dose,
            'nh3_loading_mmol_per_day':la,
            'famotidine_loading_mmol_per_day':lf,
            'joint_loading_mmol_per_day':lj,
            'nh3_fraction_of_joint_loading':la/lj,
            'overall_active_hits':len(active),
            'language_rows':len(family),
            'language_active_rows':len(active_family),
            'language_mean_abs_offset':sum(vals)/len(vals),
            'language_median_abs_offset':sorted(vals)[len(vals)//2],
            'language_max_abs_offset':max(vals),
            'language_mean_net_offset':sum(r['net_offset_change'] for r in family)/len(family),
            'language_total_new_breaks':sum(r['new_breaks'] for r in family),
            'language_total_restored_relations':sum(r['restored_relations'] for r in family),
            'language_total_relation_transitions':sum(r['relation_transition_count'] for r in family),
            'language_mean_pair_correspondence':sum(r['pair_correspondence'] for r in family)/len(family),
            'best_language_pair_rank':min(r['pair_rank_within_active_hits'] for r in active_family),
            'best_language_source_term':min(active_family,key=lambda r:r['pair_rank_within_active_hits'])['source_term'],
            'best_language_pair_correspondence':min(active_family,key=lambda r:r['pair_rank_within_active_hits'])['pair_correspondence'],
            'word_finding_abs_offset':wf['absolute_offset_change'],
            'word_finding_net_offset':wf['net_offset_change'],
            'word_finding_new_breaks':wf['new_breaks'],
            'word_finding_restored_relations':wf['restored_relations'],
            'word_finding_pair_rank':wf['pair_rank_within_active_hits'],
            'word_finding_pair_correspondence':wf['pair_correspondence'],
            'critical_in_language':sum(r['criticality']=='CRITICAL' for r in family),
            'high_in_language':sum(r['criticality']=='HIGH' for r in family),
            'moderate_in_language':sum(r['criticality']=='MODERATE' for r in family),
            'minor_in_language':sum(r['criticality']=='MINOR' for r in family),
            'informational_in_language':sum(r['criticality']=='INFORMATIONAL' for r in family),
        }
        summaries.append(summary)

    base=summaries[0]
    prev=None
    for s in summaries:
        s['language_mean_abs_offset_vs_famotidine_ratio']=s['language_mean_abs_offset']/base['language_mean_abs_offset']
        s['language_mean_abs_offset_percent_change_vs_famotidine']=(s['language_mean_abs_offset']/base['language_mean_abs_offset']-1)*100
        s['word_finding_abs_offset_vs_famotidine_ratio']=s['word_finding_abs_offset']/base['word_finding_abs_offset']
        s['word_finding_abs_offset_percent_change_vs_famotidine']=(s['word_finding_abs_offset']/base['word_finding_abs_offset']-1)*100
        if prev is None: s['local_slope_mean_abs_offset_per_mg']=None
        else: s['local_slope_mean_abs_offset_per_mg']=(s['language_mean_abs_offset']-prev['language_mean_abs_offset'])/(s['nh3_mg_per_day']-prev['nh3_mg_per_day'])
        prev=s

    fields=list(summaries[0].keys())
    with (out/'dose_series_summary.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(summaries)
    lang_fields=[
        'baseline_id','structure','structural_deviation','source_term','source_partition',
        'condition_state_sha256','constitutive_relation_count','initial_broken_relations',
        'restored_relations','new_breaks','residual_broken_relations','relation_transition_count',
        'initial_offset','residual_offset','net_offset_change','absolute_offset_change','direction',
        'new_break_fraction','criticality','criticality_order','reference_baseline_top_entry_index',
        'response_state_sha256','pair_correspondence','pair_js_correspondence','pair_sign_continuity',
        'pair_active_hit','relation_balance','pair_rank_within_active_hits',
        'nh3_mg_per_day','nh3_loading_mmol_per_day','joint_loading_mmol_per_day',
        'condition_top_entry_index','response_top_entry_index'
    ]
    write_csv(out/'language_family_all_doses.csv',all_language,lang_fields)
    meta={
        'runtime':'SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12',
        'lock_sha256':lock['sha256'],
        'famotidine':{'formula':fam['chemical_formula'],'dose':'40 mg','interval':'once daily','mw_g_mol':fam_mw,'loading_mmol_per_day':lf},
        'ammonia':{'formula':'NH3','interval':'once daily','mw_g_mol':amm_mw,'doses_mg_per_day':doses},
        'joint_operator':'Q_joint=(L_F*Q_F + L_A*Q_A)/(L_F+L_A); L_joint=L_F+L_A; unchanged rowwise engine computes normalize(B + L_joint*(Q_joint-G)), algebraically equal before normalization to B + L_F*(Q_F-G)+L_A*(Q_A-G).',
        'family_filter':'structure contains language-processing OR speech-planning; frozen family size=17',
        'interpretation':'structural model test burden only; NH3 mg/day values are declared retained-burden coordinates, not clinical dosing recommendations.'
    }
    (out/'RUN_METADATA.json').write_text(json.dumps(meta,indent=2,sort_keys=True)+'\n')
    (out/'run_stdout.json').write_text(json.dumps({'summary':summaries,'metadata':meta},indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PASS','doses':doses,'language_family_size':len(frozen_ids),'summary':summaries},indent=2))

if __name__=='__main__': main()
