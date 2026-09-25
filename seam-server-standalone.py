#!/usr/bin/env python3
"""
SEAM Compound Analyzer - Standalone HTTP Server (No Dependencies)
Built-in HTTP server with compound analysis
"""

import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Configuration
LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4"
ROWS = 5734
STRUCTURES = 420
PORT = 5000

# Load compounds
def load_compounds():
    try:
        db_path = Path(__file__).parent / 'SEAM_common_drugs_supplements_choice_registry_v1.json'
        with open(db_path, 'r') as f:
            data = json.load(f)
        return data['compounds']
    except Exception as e:
        print(f"Error loading compounds: {e}")
        return []

COMPOUNDS = load_compounds()
TASKS = {}
TASK_ID = 0
TASK_LOCK = threading.Lock()

class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler"""

    def do_GET(self):
        """Handle GET requests"""
        path = urlparse(self.path).path

        if path == '/health':
            self.send_json(200, {
                'status': 'ok',
                'lock_hash': LOCK_HASH,
                'compounds_loaded': len(COMPOUNDS)
            })
        elif path == '/compounds':
            self.send_json(200, {
                'count': len(COMPOUNDS),
                'compounds': COMPOUNDS
            })
        elif path.startswith('/results/'):
            task_id = path.split('/')[-1]
            if task_id in TASKS:
                task = TASKS[task_id]
                self.send_json(200, {
                    'task_id': task_id,
                    'status': task['status'],
                    'progress': task['progress'],
                    'result': task['result']
                })
            else:
                self.send_json(404, {'error': 'Task not found'})
        else:
            self.send_json(404, {'error': 'Not found'})

    def do_POST(self):
        """Handle POST requests"""
        path = urlparse(self.path).path

        if path == '/analyze':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(body)

                compounds = data.get('compounds', [])
                if not compounds:
                    return self.send_json(400, {'error': 'No compounds'})
                if len(compounds) > 50:
                    return self.send_json(400, {'error': 'Max 50 compounds'})

                # Create task
                global TASK_ID
                with TASK_LOCK:
                    TASK_ID += 1
                    task_id = f"task_{TASK_ID}"

                    task = {
                        'status': 'running',
                        'progress': 0,
                        'result': None
                    }
                    TASKS[task_id] = task

                # Start analysis thread
                thread = threading.Thread(
                    target=run_analysis,
                    args=(task_id, compounds),
                    daemon=True
                )
                thread.start()

                self.send_json(202, {
                    'task_id': task_id,
                    'status': 'running'
                })
            except Exception as e:
                self.send_json(500, {'error': str(e)})
        else:
            self.send_json(404, {'error': 'Not found'})

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def send_json(self, code, data):
        """Send JSON response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_analysis(task_id, compounds):
    """Run analysis simulation"""
    try:
        # Simulate progress (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
        for progress in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
            with TASK_LOCK:
                if task_id in TASKS:
                    TASKS[task_id]['progress'] = progress
            time.sleep(0.15)

        # Generate results with structural analysis simulation
        results = {
            'lock_sha256': LOCK_HASH,
            'rows': ROWS,
            'structures': STRUCTURES,
            'compounds_analyzed': len(compounds),
            'compounds': []
        }

        for compound in compounds:
            # Simulate structural perturbation response
            results['compounds'].append({
                'name': compound.get('generic_name'),
                'formula': compound.get('chemical_formula'),
                'category': compound.get('category'),
                'mw': 300.0,
                'dose_mg_day': 20,
                'rows_with_new_breaks': 342,
                'control_transitions': 0,
                'tiers': {
                    'MINOR': 298,
                    'MODERATE': 32,
                    'HIGH': 10,
                    'CRITICAL': 2
                },
                'target_structures': [
                    {
                        'structure': 'Structural perturbation analysis',
                        'new_breaks': 42,
                        'relations': 156,
                        'criticality': 'MODERATE'
                    }
                ]
            })

        # Final progress update
        with TASK_LOCK:
            if task_id in TASKS:
                TASKS[task_id]['result'] = results
                TASKS[task_id]['status'] = 'completed'
                TASKS[task_id]['progress'] = 100

    except Exception as e:
        with TASK_LOCK:
            if task_id in TASKS:
                TASKS[task_id]['status'] = 'failed'
                TASKS[task_id]['error'] = str(e)
        print(f"[ERROR] Analysis failed for {task_id}: {e}")

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SEAM Compound Analyzer Backend")
    print("  Standalone (No Dependencies)")
    print("="*60)
    print(f"✓ Compounds loaded: {len(COMPOUNDS)}")
    print(f"✓ Lock: {LOCK_HASH[:16]}...")
    print(f"✓ Server starting on http://localhost:{PORT}")
    print("\nOpen seam-ui-improved.html in your browser")
    print("="*60 + "\n")

    server = HTTPServer(('localhost', PORT), RequestHandler)
    server.serve_forever()
