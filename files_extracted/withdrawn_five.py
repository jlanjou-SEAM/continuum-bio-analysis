#!/usr/bin/env python3
"""Canonical result: all five market-withdrawn compounds, row level, each
against its own zero-loading control. Emits JSON for the lookup page."""
import sys, json, collections
from pathlib import Path
RT=Path(sys.argv[1] if len(sys.argv)>1 else
  '/tmp/SEAM_Famotidine_Ammonia_Perturbation_Engineering_Archive_v1/02_runtime_extracted/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12')
sys.path.insert(0,str(RT))
from engine.full_sider import load_lock, build_compound_projection, molecular_weight
from engine.rowwise import run_condition_matrix
lock=load_lock(RT/'data/prescreen.lock')
LOCK_SHA='62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4'
assert lock['sha256']==LOCK_SHA, 'LOCK HASH MISMATCH'
CASES=[
 ('terfenadine','C32H41NO2',120,'withdrawn','QT prolongation / torsades de pointes',
  ['cardiac','myocard','ventricul','atrioventric','sinoatrial','cardiomyocyte']),
 ('cisapride','C23H29ClFN3O4',40,'withdrawn','QT prolongation / torsades de pointes',
  ['cardiac','myocard','ventricul','atrioventric','sinoatrial','cardiomyocyte']),
 ('rofecoxib','C17H14O4S',25,'withdrawn','thrombotic cardiovascular events',
  ['platelet','thromb','hemostas','coagul']),
 ('cerivastatin','C26H34FNO5',0.4,'withdrawn','rhabdomyolysis',
  ['skeletal-muscle','musculoskelet']),
 ('troglitazone','C24H27NO5S',400,'withdrawn','hepatocellular injury',
  ['hepat','biliar','bile']),
 ('famotidine','C8H15N7O2S3',40,'marketed','no cardiac profile',
  ['cardiac','myocard','ventricul','atrioventric','sinoatrial','cardiomyocyte']),
 ('albuterol','C13H21NO3',10,'marketed','palpitations / blood pressure; no arrhythmia',
  ['cardiac','myocard','ventricul','atrioventric','sinoatrial','cardiomyocyte']),
]
out={'lock_sha256':lock['sha256'],'rows':lock['row_count'],
     'structures':lock['structure_count'],'compounds':[]}
for name,f,mg,status,known,keys in CASES:
    Q=build_compound_projection(lock,f); mw=molecular_weight(f)[0]; lam=mg/mw
    ctl=sum(1 for r in run_condition_matrix(lock,Q,0.0)['rows'] if r['relation_transition_count']>0)
    rows=run_condition_matrix(lock,Q,lam)['rows']
    hit=[r for r in rows if r['new_breaks']>0]
    sel=[r for r in hit if any(k in r['structure'].lower() for k in keys)]
    tops=sorted({(r['new_breaks'],r['constitutive_relation_count'],r['structure'],r['criticality'])
                 for r in sel},reverse=True)[:6]
    out['compounds'].append(dict(
        name=name,formula=f,mw=round(mw,3),dose_mg_day=mg,loading_mmol_day=round(lam,6),
        status=status,known_effect=known,projection_sha256=Q['coordinate_sha256'],
        control_transitions=ctl,rows_with_new_breaks=len(hit),
        tiers=dict(collections.Counter(r['criticality'] for r in hit)),
        target_rows=len(sel),
        target_structures=[dict(new_breaks=nb,relations=rel,structure=s,criticality=c)
                           for nb,rel,s,c in tops]))
    print(f'{name:<14} ctl={ctl} breaks={len(hit):>5} target={len(sel):>4} top={tops[0][0]}/{tops[0][1] if tops else 0}')
json.dump(out,open(Path(__file__).parent.parent/'results'/'withdrawn_five.json','w'),indent=1)
print('\nwrote results/withdrawn_five.json')
