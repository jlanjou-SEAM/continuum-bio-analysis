#!/usr/bin/env python3
"""
SEAM Structural Perturbation Analysis Backend
Enhanced API Server with execution handling and result caching

Endpoints:
  GET  /health              - Health check
  GET  /compounds           - Get compound library (306 compounds)
  POST /analyze             - Submit compound selection for analysis
  GET  /results/{task_id}   - Poll for analysis results
  POST /cancel/{task_id}    - Cancel ongoing analysis
"""

import os
import sys
import json
import subprocess
import argparse
import hashlib
import tempfile
import threading
import time
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from collections import defaultdict

app = Flask(__name__)
CORS(app)

# Configuration
LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4"
ROWS = 5734
STRUCTURES = 420
RUNTIME_PATH = None
RUNNER_SCRIPT = None

# Task tracking for async execution
tasks = {}
tasks_lock = threading.Lock()

class AnalysisTask:
    """Manages a single analysis job"""
    def __init__(self, task_id, compounds):
        self.task_id = task_id
        self.compounds = compounds
        self.status = "queued"  # queued, running, completed, failed
        self.progress = 0
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.started_at = None
        self.completed_at = None

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "compound_count": len(self.compounds),
            "result": self.result,
            "error": self.error
        }

def generate_task_id(compounds):
    """Generate unique task ID"""
    compound_str = "|".join(sorted([c["generic_name"] for c in compounds]))
    return hashlib.sha256(compound_str.encode()).hexdigest()[:16]

@app.route('/health', methods=['GET'])
def health():
    """Health check and configuration status"""
    return jsonify({
        'status': 'ok',
        'lock_hash': LOCK_HASH,
        'rows': ROWS,
        'structures': STRUCTURES,
        'runtime_configured': RUNTIME_PATH is not None and os.path.exists(RUNTIME_PATH),
        'runner_available': RUNNER_SCRIPT is not None and os.path.exists(RUNNER_SCRIPT),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/compounds', methods=['GET'])
def get_compounds():
    """Get complete compound library (306 compounds)"""
    try:
        compound_file = Path(__file__).parent / 'SEAM_common_drugs_supplements_choice_registry_v1.json'
        with open(compound_file, 'r') as f:
            data = json.load(f)

        return jsonify({
            'count': len(data['compounds']),
            'schema': data['schema'],
            'compounds': data['compounds']
        })
    except Exception as e:
        return jsonify({'error': f'Failed to load compounds: {str(e)}'}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Submit compounds for SEAM analysis

    Request body:
    {
        "compounds": [
            {
                "generic_name": "famotidine",
                "chemical_formula": "C8H15N7O2S3",
                "category": "Drug - Gastrointestinal"
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        compounds = data.get('compounds', [])

        if not compounds:
            return jsonify({'error': 'No compounds provided'}), 400

        if len(compounds) > 50:
            return jsonify({'error': 'Maximum 50 compounds per analysis'}), 400

        # Generate task ID
        task_id = generate_task_id(compounds)

        # Check if already running
        with tasks_lock:
            if task_id in tasks:
                task = tasks[task_id]
                if task.status in ['running', 'queued']:
                    return jsonify({
                        'task_id': task_id,
                        'status': task.status,
                        'message': 'Analysis already in progress for this compound set'
                    }), 202

        # Create new task
        task = AnalysisTask(task_id, compounds)
        with tasks_lock:
            tasks[task_id] = task

        # Launch analysis in background thread
        thread = threading.Thread(
            target=execute_analysis,
            args=(task_id, compounds),
            daemon=True
        )
        thread.start()

        return jsonify({
            'task_id': task_id,
            'status': 'queued',
            'message': 'Analysis queued. Poll /results/{task_id} for progress.'
        }), 202

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<task_id>', methods=['GET'])
def get_results(task_id):
    """Get status and results of an analysis task"""
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': 'Task not found'}), 404

        task = tasks[task_id]
        return jsonify(task.to_dict())

@app.route('/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """Cancel an ongoing analysis"""
    with tasks_lock:
        if task_id not in tasks:
            return jsonify({'error': 'Task not found'}), 404

        task = tasks[task_id]
        if task.status not in ['queued', 'running']:
            return jsonify({'error': f'Cannot cancel task with status: {task.status}'}), 400

        task.status = 'cancelled'
        task.error = 'Cancelled by user'

    return jsonify({'task_id': task_id, 'status': 'cancelled'})

def execute_analysis(task_id, compounds):
    """Execute SEAM analysis (runs in background thread)"""
    with tasks_lock:
        task = tasks[task_id]
        task.status = 'running'
        task.started_at = datetime.now()
        task.progress = 10

    try:
        # Placeholder: In production, this would call withdrawn_five.py runner
        # with the specific compounds and collect results

        # For now, simulate analysis
        time.sleep(2)  # Simulate processing

        results = {
            'lock_sha256': LOCK_HASH,
            'rows': ROWS,
            'structures': STRUCTURES,
            'compounds_analyzed': len(compounds),
            'compounds': []
        }

        # Build result for each compound
        for i, compound in enumerate(compounds):
            results['compounds'].append({
                'name': compound.get('generic_name'),
                'formula': compound.get('chemical_formula'),
                'category': compound.get('category'),
                'status': 'pending',
                'note': 'Results pending: configure runtime path to enable SEAM execution'
            })

            with tasks_lock:
                task.progress = 10 + (i + 1) * (80 // len(compounds))

        # Mark complete
        with tasks_lock:
            task.status = 'completed'
            task.progress = 100
            task.result = results
            task.completed_at = datetime.now()

    except Exception as e:
        with tasks_lock:
            task.status = 'failed'
            task.error = str(e)
            task.completed_at = datetime.now()

@app.route('/docs', methods=['GET'])
def docs():
    """API Documentation"""
    return jsonify({
        'title': 'SEAM Structural Perturbation Backend API',
        'version': '2.0',
        'description': 'Backend engine for compound selection and SEAM analysis',
        'lock_hash': LOCK_HASH,
        'endpoints': {
            'GET /health': 'Health check and server status',
            'GET /compounds': 'Get 306-compound library',
            'POST /analyze': 'Submit compounds for analysis (async)',
            'GET /results/<task_id>': 'Poll analysis progress and results',
            'POST /cancel/<task_id>': 'Cancel ongoing analysis',
            'GET /docs': 'This documentation'
        },
        'architecture': 'Frontend communicates only via API, never directly with SEAM engine',
        'max_compounds_per_analysis': 50
    })

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='SEAM Structural Perturbation Analysis Backend'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run server on (default: 5000)'
    )
    parser.add_argument(
        '--runtime',
        type=str,
        help='Path to SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12'
    )
    parser.add_argument(
        '--runner',
        type=str,
        help='Path to withdrawn_five.py runner script'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )

    args = parser.parse_args()

    global RUNTIME_PATH, RUNNER_SCRIPT
    RUNTIME_PATH = args.runtime
    RUNNER_SCRIPT = args.runner

    print(f"╔════════════════════════════════════════════════════════╗")
    print(f"║  SEAM Structural Perturbation Analysis Backend        ║")
    print(f"║  Version 2.0 - Split Architecture                    ║")
    print(f"╚════════════════════════════════════════════════════════╝")
    print()
    print(f"Lock Hash:     {LOCK_HASH}")
    print(f"Runtime:       {RUNTIME_PATH or 'Not configured'}")
    print(f"Runner:        {RUNNER_SCRIPT or 'Not configured'}")
    print(f"Port:          {args.port}")
    print()
    print(f"API Endpoints:")
    print(f"  Health:      http://localhost:{args.port}/health")
    print(f"  Compounds:   http://localhost:{args.port}/compounds")
    print(f"  API Docs:    http://localhost:{args.port}/docs")
    print()
    print(f"Frontend should connect to: http://localhost:{args.port}")
    print()

    app.run(
        host='localhost',
        port=args.port,
        debug=args.debug
    )

if __name__ == '__main__':
    main()
