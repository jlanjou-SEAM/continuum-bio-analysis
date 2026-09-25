#!/usr/bin/env python3
"""Continuum Bio Analysis - Comparative Mode with Baseline/Differential"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4"
ROWS = 5734
STRUCTURES = 420
PORT = 5000

# Load compounds, structures, conditions
with open('SEAM_common_drugs_supplements_choice_registry_v1.json', 'r') as f:
    COMPOUNDS = json.load(f).get('compounds', [])
print(f"[INIT] Loaded {len(COMPOUNDS)} compounds")

with open('structure_database.json', 'r') as f:
    STRUCTURES_DATA = json.load(f).get('compound_structures', {})
print(f"[INIT] Loaded structure data")

with open('conditions_database.json', 'r') as f:
    conditions_raw = json.load(f).get('conditions', [])
    CONDITIONS_DATA = {cond['generic_name']: cond for cond in conditions_raw}
print(f"[INIT] Loaded {len(CONDITIONS_DATA)} conditions")

TASKS = {}
NEXT_TASK_ID = 0

def get_structures_for_item(item):
    """Get structures for a compound or condition"""
    name = item.get('generic_name', 'Unknown')
    if name in CONDITIONS_DATA:
        return CONDITIONS_DATA[name].get('target_structures', [])
    else:
        return STRUCTURES_DATA.get(name, STRUCTURES_DATA.get('_default', []))

def merge_and_sort_structures(all_structures):
    """Merge structures and sort by severity"""
    severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'MINOR': 3}
    all_structures.sort(key=lambda x: severity_order.get(x['criticality'], 99))

    aggregate_tiers = {'CRITICAL': 0, 'HIGH': 0, 'MODERATE': 0, 'MINOR': 0}
    total_breaks = 0
    for struct in all_structures:
        crit = struct['criticality']
        if crit in aggregate_tiers:
            aggregate_tiers[crit] += 1
        total_breaks += struct['new_breaks']

    return all_structures, aggregate_tiers, total_breaks

def analyze_compounds(task_id, comp_list):
    """Analyze compounds"""
    try:
        for p in [10, 30, 50, 70, 90]:
            if task_id in TASKS:
                TASKS[task_id]['progress'] = p
            time.sleep(0.15)

        # Build structures
        all_structures = []
        for compound in comp_list:
            structures = get_structures_for_item(compound)
            for struct in structures:
                all_structures.append({
                    'structure': struct['structure'],
                    'new_breaks': struct['new_breaks'],
                    'relations': struct['relations'],
                    'criticality': struct['criticality'],
                    'source': compound.get('generic_name', 'Unknown')
                })

        merged, tiers, total_breaks = merge_and_sort_structures(all_structures)

        if task_id in TASKS:
            TASKS[task_id]['result'] = {
                'lock_sha256': LOCK_HASH,
                'rows': ROWS,
                'structures': STRUCTURES,
                'compounds_analyzed': len(comp_list),
                'all_structures_merged': merged,
                'aggregate_tiers': tiers,
                'total_structural_impacts': len(merged),
                'total_breaks_combined': total_breaks
            }
            TASKS[task_id]['status'] = 'completed'
            TASKS[task_id]['progress'] = 100
            print(f"[SUCCESS] Task {task_id} completed")

    except Exception as ex:
        print(f"[ERROR] Task {task_id}: {ex}")
        if task_id in TASKS:
            TASKS[task_id]['status'] = 'failed'
            TASKS[task_id]['error'] = str(ex)

def analyze_comparative(task_id, conditions, compounds):
    """Comparative analysis: baseline (conditions only) + differential (with compounds)"""
    try:
        # Run 1: Baseline (conditions only)
        for p in [10, 20, 30]:
            if task_id in TASKS:
                TASKS[task_id]['progress'] = p
            time.sleep(0.1)

        baseline_structures = []
        for cond in conditions:
            structures = get_structures_for_item(cond)
            for struct in structures:
                baseline_structures.append({
                    'structure': struct['structure'],
                    'new_breaks': struct['new_breaks'],
                    'relations': struct['relations'],
                    'criticality': struct['criticality'],
                    'source': cond.get('generic_name', 'Unknown')
                })

        baseline_merged, baseline_tiers, baseline_breaks = merge_and_sort_structures(baseline_structures.copy())

        # Run 2: Total (conditions + compounds)
        for p in [40, 50, 60, 70, 80, 90]:
            if task_id in TASKS:
                TASKS[task_id]['progress'] = p
            time.sleep(0.1)

        total_structures = baseline_structures.copy()
        for compound in compounds:
            structures = get_structures_for_item(compound)
            for struct in structures:
                total_structures.append({
                    'structure': struct['structure'],
                    'new_breaks': struct['new_breaks'],
                    'relations': struct['relations'],
                    'criticality': struct['criticality'],
                    'source': compound.get('generic_name', 'Unknown')
                })

        total_merged, total_tiers, total_breaks = merge_and_sort_structures(total_structures)

        # Calculate differential
        baseline_names = {s['structure'] for s in baseline_merged}
        differential = [s for s in total_merged if s['structure'] not in baseline_names]

        if task_id in TASKS:
            TASKS[task_id]['result'] = {
                'lock_sha256': LOCK_HASH,
                'rows': ROWS,
                'structures': STRUCTURES,
                'analysis_mode': 'comparative',
                'baseline': {
                    'structures': baseline_merged,
                    'tiers': baseline_tiers,
                    'total_impacts': len(baseline_merged),
                    'total_breaks': baseline_breaks
                },
                'differential': {
                    'structures': differential,
                    'new_impacts': len(differential)
                },
                'total': {
                    'structures': total_merged,
                    'tiers': total_tiers,
                    'total_impacts': len(total_merged),
                    'total_breaks': total_breaks
                },
                'compounds_analyzed': len(conditions) + len(compounds)
            }
            TASKS[task_id]['status'] = 'completed'
            TASKS[task_id]['progress'] = 100
            print(f"[SUCCESS] Comparative task {task_id} completed")

    except Exception as ex:
        print(f"[ERROR] Comparative task {task_id}: {ex}")
        if task_id in TASKS:
            TASKS[task_id]['status'] = 'failed'
            TASKS[task_id]['error'] = str(ex)

class APIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split('?')[0]

        if path == '/health':
            self.send_json({'status': 'ok', 'lock_hash': LOCK_HASH, 'compounds': len(COMPOUNDS)})
        elif path == '/compounds':
            self.send_json({'count': len(COMPOUNDS), 'compounds': COMPOUNDS})
        elif path == '/conditions':
            self.send_json({'count': len(CONDITIONS_DATA), 'conditions': list(CONDITIONS_DATA.values())})
        elif path.startswith('/results/'):
            task_id = path.split('/')[-1]
            if task_id in TASKS:
                task = TASKS[task_id]
                self.send_json({
                    'task_id': task_id,
                    'status': task['status'],
                    'progress': task['progress'],
                    'result': task['result']
                })
            else:
                self.send_json({'error': 'Not found'}, 404)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        path = self.path.split('?')[0]

        if path == '/analyze':
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len).decode()
                data = json.loads(body)

                comp_list = data.get('compounds', [])
                if not comp_list or len(comp_list) > 50:
                    self.send_json({'error': 'Invalid compounds'}, 400)
                    return

                global NEXT_TASK_ID
                NEXT_TASK_ID += 1
                task_id = f"task_{NEXT_TASK_ID}"

                TASKS[task_id] = {'status': 'running', 'progress': 0, 'result': None, 'error': None}

                # Separate conditions from compounds
                conditions = [c for c in comp_list if c.get('category') == 'Condition']
                compounds = [c for c in comp_list if c.get('category') != 'Condition']

                # Route to appropriate analysis
                if conditions:
                    thread = threading.Thread(target=analyze_comparative, args=(task_id, conditions, compounds), daemon=True)
                else:
                    thread = threading.Thread(target=analyze_compounds, args=(task_id, compounds), daemon=True)

                thread.start()
                self.send_json({'task_id': task_id, 'status': 'running'}, 202)

            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.add_cors()
        self.end_headers()

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.add_cors()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def add_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, *args):
        pass

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Continuum Bio Analysis - Comparative Mode")
    print("="*60)
    print(f"✓ Lock: {LOCK_HASH[:20]}...")
    print(f"✓ Compounds: {len(COMPOUNDS)}")
    print(f"✓ Conditions: {len(CONDITIONS_DATA)}")
    print(f"✓ Server: http://localhost:{PORT}")
    print("="*60 + "\n")

    HTTPServer(('localhost', PORT), APIHandler).serve_forever()
