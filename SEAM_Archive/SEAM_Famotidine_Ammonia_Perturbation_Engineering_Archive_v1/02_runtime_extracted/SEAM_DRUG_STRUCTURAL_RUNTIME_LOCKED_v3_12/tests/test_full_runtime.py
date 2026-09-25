from pathlib import Path
import tempfile, json, math
from engine.full_sider import load_lock
from engine.inputs import parse_interval, resolve_compound
from engine.rowwise import build_condition_state, run_condition_matrix
from engine.pairwise import pair_correspondence, resolve_pair_matrix
from engine.run import run

ROOT=Path(__file__).resolve().parents[1]


def test_lock_shape():
    d=load_lock(ROOT/'data/prescreen.lock')
    assert d['row_count']==5734
    assert d['structure_count']==420
    assert d['manifold_count']==232
    assert d['pair_count']==54205


def test_registry_name_and_direct_formula_resolve_same_projection():
    d=load_lock(ROOT/'data/prescreen.lock')
    named=resolve_compound('Albuterol',ROOT,d)
    direct=resolve_compound('C13H21NO3',ROOT,d)
    assert named['chemical_formula']=='C13H21NO3'
    assert named['manifold_projection']['coordinates']==direct['manifold_projection']['coordinates']
    assert named['manifold_projection']['coordinate_sha256']==direct['manifold_projection']['coordinate_sha256']


def test_condition_rows_are_constructed_independently_not_expanded_from_420_result():
    d=load_lock(ROOT/'data/prescreen.lock')
    a=build_condition_state(d,d['rows'][10])
    b=build_condition_state(d,d['rows'][11])
    assert d['rows'][10]['structure_idx']==d['rows'][11]['structure_idx']
    assert a['state_sha256'] != b['state_sha256']
    c=build_condition_state(d,d['rows'][12])
    assert b['state_sha256'] == c['state_sha256']


def test_compound_identity_independent_of_exposure():
    d=load_lock(ROOT/'data/prescreen.lock')
    a=resolve_compound('Albuterol',ROOT,d)['manifold_projection']
    b=resolve_compound('Famotidine',ROOT,d)['manifold_projection']
    assert a['coordinate_sha256'] != b['coordinate_sha256']
    assert parse_interval('once daily')['interval_seconds'] != parse_interval('every 6 hours')['interval_seconds']


def test_pair_operator_exact_identity_closure():
    p=[0.1,0.2,0.3,0.4]
    score,js,sc=pair_correspondence(p,p)
    assert abs(js-1.0) < 1e-12
    assert abs(sc-1.0) < 1e-12
    assert abs(score-1.0) < 1e-12


def test_pair_aliases_share_pair_correspondence_when_condition_state_is_same():
    d=load_lock(ROOT/'data/prescreen.lock')
    proj=resolve_compound('Famotidine',ROOT,d)['manifold_projection']
    rowwise=run_condition_matrix(d,proj,40.0/337.4454)
    paired=resolve_pair_matrix(d,proj,rowwise['rows'])
    byid={x['baseline_id']:x for x in paired['rows']}
    # SB0012/SB0013 share the same structure + deviation but different source terms.
    assert byid['SB0012']['condition_state_sha256']==byid['SB0013']['condition_state_sha256']
    assert abs(byid['SB0012']['pair_correspondence']-byid['SB0013']['pair_correspondence']) < 1e-15


def test_zero_loading_produces_no_hit_and_pair_resolution_cannot_create_one():
    d=load_lock(ROOT/'data/prescreen.lock')
    p=resolve_compound('C32H41NO2',ROOT,d)['manifold_projection']
    rowwise=run_condition_matrix(d,p,0.0)
    assert len(rowwise['rows'])==5734
    assert sum(x['restored_relations'] for x in rowwise['rows'])==0
    assert sum(x['new_breaks'] for x in rowwise['rows'])==0
    paired=resolve_pair_matrix(d,p,rowwise['rows'])
    assert paired['counts']['pair_rows_evaluated']==5734
    assert paired['counts']['pair_ranked_active_hits']==0
    assert all(not x['pair_active_hit'] for x in paired['rows'])


def test_pair_ranking_is_pair_score_only_among_saved_active_hits():
    d=load_lock(ROOT/'data/prescreen.lock')
    p=resolve_compound('Famotidine',ROOT,d)['manifold_projection']
    rowwise=run_condition_matrix(d,p,40.0/337.4454)
    paired=resolve_pair_matrix(d,p,rowwise['rows'])
    active=paired['pair_ranked_active_hits']
    assert len(active)==rowwise['counts']['rows_with_relation_transition']
    assert all(active[i]['pair_correspondence'] >= active[i+1]['pair_correspondence']-1e-15 for i in range(len(active)-1))
    assert all(x['relation_transition_count']>0 for x in active)


def test_end_to_end_single_compound_question_is_5734_rowwise_plus_pair_resolution():
    with tempfile.TemporaryDirectory() as td:
        r=run('Famotidine','40 mg','once daily',td,make_pdf=False)
        assert r['matrix']['condition_rows']==5734
        assert r['matrix']['parent_constitutive_templates']==420
        assert r['matrix']['evaluation_mode']=='ROWWISE_5734_PLUS_PAIR_RESOLUTION'
        assert r['counts']['condition_states_evaluated']==5734
        assert r['counts']['pair_rows_evaluated']==5734
        assert r['counts']['pair_ranked_active_hits']==r['counts']['rows_with_relation_transition']
        assert len(r['all_rows'])==5734
        assert r['ranking_contract']['cross_compound_comparison'] is False
        assert r['primary_effects'][0]['pair_rank_within_active_hits']==1
        p4=Path(td)/'process/04_rowwise_condition_comparison.json'
        p5=Path(td)/'process/05_pair_resolution.json'
        assert p4.exists() and p5.exists()
        mid=json.loads(p5.read_text())
        assert mid['condition_rows']==5734
        assert mid['active_hit_count']==r['counts']['rows_with_relation_transition']
        assert len(mid['rows'])==5734


def test_repeated_parent_structure_can_return_different_row_effects():
    d=load_lock(ROOT/'data/prescreen.lock')
    p=resolve_compound('Famotidine',ROOT,d)['manifold_projection']
    r=run_condition_matrix(d,p,40.0/337.4454)
    byid={x['baseline_id']:x for x in r['rows']}
    a,b=byid['SB0011'],byid['SB0012']
    assert a['structure']==b['structure']
    assert a['condition_state_sha256'] != b['condition_state_sha256']
    assert (a['net_offset_change'],a['new_breaks'],a['restored_relations']) != (b['net_offset_change'],b['new_breaks'],b['restored_relations'])


def test_direct_formula_absent_name_registry_runs():
    with tempfile.TemporaryDirectory() as td:
        r=run('C32H41NO2','60 mg','once daily',td,make_pdf=False)
        assert r['chemical_formula']=='C32H41NO2'
        assert r['matrix']['condition_rows']==5734
        assert r['counts']['pair_rows_evaluated']==5734
