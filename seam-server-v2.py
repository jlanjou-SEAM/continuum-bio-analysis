#!/usr/bin/env python3
"""Continuum Bio Analysis - Simplified Backend"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4"
ROWS = 5734
STRUCTURES = 420
PORT = 5000

# Load compounds
try:
    with open('SEAM_common_drugs_supplements_choice_registry_v1.json', 'r') as f:
        COMPOUNDS = json.load(f).get('compounds', [])
    print(f"[INIT] Loaded {len(COMPOUNDS)} compounds")
except:
    print("[WARN] Could not load compound database - using empty list")
    COMPOUNDS = []

# Load structure data
try:
    with open('structure_database.json', 'r') as f:
        STRUCTURES_DATA = json.load(f).get('compound_structures', {})
    print(f"[INIT] Loaded structure data for {len(STRUCTURES_DATA)-1} compounds")
except:
    print("[WARN] Could not load structure database")
    STRUCTURES_DATA = {}

# Load conditions database
try:
    with open('conditions_database.json', 'r') as f:
        conditions_raw = json.load(f).get('conditions', [])
        CONDITIONS_DATA = {cond['generic_name']: cond for cond in conditions_raw}
    print(f"[INIT] Loaded {len(CONDITIONS_DATA)} conditions with structural data")
except:
    print("[WARN] Could not load conditions database")
    CONDITIONS_DATA = {}

TASKS = {}
NEXT_TASK_ID = 0

def analyze_compounds(task_id, comp_list):
    """Perform analysis - simulation with full error handling"""
    print(f"[ANALYZE] Starting task {task_id} with {len(comp_list)} compounds")

    try:
        # Check task exists
        if task_id not in TASKS:
            print(f"[ERROR] Task {task_id} not in TASKS!")
            return

        task = TASKS[task_id]

        # Simulate progress
        for progress_pct in [10, 30, 50, 70, 90]:
            print(f"[ANALYZE] {task_id}: Setting progress to {progress_pct}%")
            if task_id in TASKS:
                TASKS[task_id]['progress'] = progress_pct
            time.sleep(0.15)

        # Verify task still exists
        if task_id not in TASKS:
            print(f"[ERROR] Task {task_id} disappeared!")
            return

        task = TASKS[task_id]
        print(f"[ANALYZE] {task_id}: Building results...")

        # Build results
        results_compounds = []
        for compound in comp_list:
            comp_name = compound.get('generic_name', 'Unknown')

            # Check if this is a condition
            if comp_name in CONDITIONS_DATA:
                # Use condition-specific structural perturbations
                structures = CONDITIONS_DATA[comp_name].get('target_structures', [])
                category = "Condition"
                formula = "condition"
            else:
                # Get structure data for regular compounds
                structures = STRUCTURES_DATA.get(comp_name, STRUCTURES_DATA.get('_default', []))
                category = compound.get('category', 'Unknown')
                formula = compound.get('chemical_formula', 'N/A')

            # Count tiers from structures
            tiers = {'MINOR': 0, 'MODERATE': 0, 'HIGH': 0, 'CRITICAL': 0}
            total_breaks = 0
            for struct in structures:
                criticality = struct.get('criticality', 'MINOR')
                if criticality in tiers:
                    tiers[criticality] += 1
                total_breaks += struct.get('new_breaks', 0)

            results_compounds.append({
                'name': comp_name,
                'formula': formula,
                'category': category,
                'mw': 300.0,
                'dose_mg_day': 20,
                'rows_with_new_breaks': total_breaks,
                'control_transitions': 0,
                'tiers': tiers,
                'target_structures': structures
            })

        print(f"[ANALYZE] {task_id}: Merging and sorting structures...")

        # Merge all structures from all compounds into a single list
        all_structures = []
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MODERATE': 2, 'MINOR': 3}

        for compound_result in results_compounds:
            for struct in compound_result.get('target_structures', []):
                all_structures.append({
                    'structure': struct['structure'],
                    'new_breaks': struct['new_breaks'],
                    'relations': struct['relations'],
                    'criticality': struct['criticality'],
                    'source': compound_result['name']  # Track which compound/condition caused it
                })

        # Sort by severity (CRITICAL first, then HIGH, MODERATE, MINOR)
        all_structures.sort(key=lambda x: severity_order.get(x['criticality'], 99))

        # Calculate aggregate tiers
        aggregate_tiers = {'CRITICAL': 0, 'HIGH': 0, 'MODERATE': 0, 'MINOR': 0}
        total_breaks = 0
        for struct in all_structures:
            crit = struct['criticality']
            if crit in aggregate_tiers:
                aggregate_tiers[crit] += 1
            total_breaks += struct['new_breaks']

        print(f"[ANALYZE] {task_id}: Setting result...")
        task['result'] = {
            'lock_sha256': LOCK_HASH,
            'rows': ROWS,
            'structures': STRUCTURES,
            'compounds_analyzed': len(comp_list),
            'compounds': results_compounds,
            'all_structures_merged': all_structures,
            'aggregate_tiers': aggregate_tiers,
            'total_structural_impacts': len(all_structures),
            'total_breaks_combined': total_breaks
        }
        task['status'] = 'completed'
        task['progress'] = 100
        print(f"[SUCCESS] Task {task_id} completed with {len(all_structures)} merged structures!")

    except Exception as ex:
        print(f"[ERROR] Task {task_id} exception: {type(ex).__name__}: {ex}")
        if task_id in TASKS:
            TASKS[task_id]['status'] = 'failed'
            TASKS[task_id]['error'] = str(ex)

class APIHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split('?')[0]

        if path == '/health':
            response = {
                'status': 'ok',
                'lock_hash': LOCK_HASH,
                'compounds_loaded': len(COMPOUNDS)
            }
            self.send_json_response(response)

        elif path == '/compounds':
            response = {
                'count': len(COMPOUNDS),
                'compounds': COMPOUNDS
            }
            self.send_json_response(response)

        elif path == '/conditions':
            conditions_list = list(CONDITIONS_DATA.values())
            response = {
                'count': len(conditions_list),
                'conditions': conditions_list
            }
            self.send_json_response(response)

        elif path.startswith('/results/'):
            task_id = path.split('/')[-1]
            if task_id in TASKS:
                task = TASKS[task_id]
                response = {
                    'task_id': task_id,
                    'status': task['status'],
                    'progress': task['progress'],
                    'result': task['result']
                }
                self.send_json_response(response)
            else:
                self.send_json_response({'error': 'Task not found'}, 404)
        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def do_POST(self):
        path = self.path.split('?')[0]

        if path == '/analyze':
            try:
                content_len = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_len).decode()
                data = json.loads(body)

                compound_list = data.get('compounds', [])
                if not compound_list:
                    self.send_json_response({'error': 'No compounds provided'}, 400)
                    return

                if len(compound_list) > 50:
                    self.send_json_response({'error': 'Max 50 compounds'}, 400)
                    return

                # Create task
                global NEXT_TASK_ID
                NEXT_TASK_ID += 1
                task_id = f"task_{NEXT_TASK_ID}"

                TASKS[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'result': None,
                    'error': None
                }

                print(f"[API] Created task {task_id} with {len(compound_list)} compounds")

                # Start background analysis
                thread = threading.Thread(
                    target=analyze_compounds,
                    args=(task_id, compound_list),
                    daemon=True
                )
                thread.start()

                self.send_json_response(
                    {'task_id': task_id, 'status': 'running'},
                    202
                )

            except Exception as e:
                print(f"[ERROR] POST /analyze failed: {e}")
                self.send_json_response({'error': str(e)}, 500)
        else:
            self.send_json_response({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.add_cors_headers()
        self.end_headers()

    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.add_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def add_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, format, *args):
        pass  # Suppress default logging

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Continuum Bio Analysis")
    print("  Backend Server")
    print("="*60)
    print(f"✓ Lock: {LOCK_HASH[:20]}...")
    print(f"✓ Compounds: {len(COMPOUNDS)} loaded")
    print(f"✓ Server: http://localhost:{PORT}")
    print("="*60 + "\n")

    server = HTTPServer(('localhost', PORT), APIHandler)
    server.serve_forever()
