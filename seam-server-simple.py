#!/usr/bin/env python3
"""SEAM Backend - Simplified version"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4"
ROWS = 5734
STRUCTURES = 420
PORT = 5000

# Load compounds from JSON
try:
    with open('SEAM_common_drugs_supplements_choice_registry_v1.json', 'r') as f:
        data = json.load(f)
    COMPOUNDS = data['compounds']
    print(f"[INIT] Loaded {len(COMPOUNDS)} compounds")
except Exception as e:
    print(f"[WARN] Could not load compound database: {e}")
    COMPOUNDS = []

# Task storage
TASKS = {}
NEXT_ID = 0

def run_analysis(task_id, compound_list):
    """Run analysis - simulated"""
    task = TASKS[task_id]

    try:
        # Progress: 10%, 30%, 50%, 70%, 90%
        for pct in [10, 30, 50, 70, 90]:
            task['progress'] = pct
            time.sleep(0.2)

        # Build result
        compounds_data = []
        for comp in compound_list:
            compounds_data.append({
                'name': comp.get('generic_name', 'Unknown'),
                'formula': comp.get('chemical_formula', 'N/A'),
                'category': comp.get('category', 'Unknown'),
                'mw': 300.0,
                'dose_mg_day': 20,
                'rows_with_new_breaks': 342,
                'control_transitions': 0,
                'tiers': {'MINOR': 298, 'MODERATE': 32, 'HIGH': 10, 'CRITICAL': 2},
                'target_structures': [{
                    'structure': 'Structural perturbation analysis',
                    'new_breaks': 42,
                    'relations': 156,
                    'criticality': 'MODERATE'
                }]
            })

        task['result'] = {
            'lock_sha256': LOCK_HASH,
            'rows': ROWS,
            'structures': STRUCTURES,
            'compounds_analyzed': len(compound_list),
            'compounds': compounds_data
        }
        task['status'] = 'completed'
        task['progress'] = 100

    except Exception as e:
        task['status'] = 'failed'
        task['error'] = str(e)
        print(f"[ERROR] Task {task_id} failed: {e}")

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split('?')[0]

        if path == '/health':
            self.send_json({'status': 'ok', 'lock_hash': LOCK_HASH, 'compounds_loaded': len(COMPOUNDS)})
        elif path == '/compounds':
            self.send_json({'count': len(COMPOUNDS), 'compounds': COMPOUNDS})
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
                length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(length).decode()
                data = json.loads(body)

                compounds = data.get('compounds', [])
                if not compounds:
                    self.send_json({'error': 'No compounds'}, 400)
                    return

                global NEXT_ID
                NEXT_ID += 1
                task_id = f"task_{NEXT_ID}"

                TASKS[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'result': None,
                    'error': None
                }

                # Start analysis in background
                t = threading.Thread(target=run_analysis, args=(task_id, compounds), daemon=True)
                t.start()

                self.send_json({'task_id': task_id, 'status': 'running'}, 202)

            except Exception as e:
                self.send_json({'error': str(e)}, 500)
        else:
            self.send_json({'error': 'Not found'}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  Continuum Bio Analysis")
    print("  HTTP Server")
    print("="*60)
    print(f"✓ Lock: {LOCK_HASH[:16]}...")
    print(f"✓ Compounds: {len(COMPOUNDS)}")
    print(f"✓ Server: http://localhost:{PORT}")
    print("="*60 + "\n")

    server = HTTPServer(('localhost', PORT), Handler)
    server.serve_forever()
