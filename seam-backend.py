#!/usr/bin/env python3
"""
SEAM Compound Analyzer Backend
Simple Flask API for compound selection and analysis
"""

import os
import json
import threading
import time
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
LOCK_HASH = "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4"
ROWS = 5734
STRUCTURES = 420

# In-memory task storage
tasks = {}
task_counter = 0

def load_compounds():
    """Load compound database"""
    try:
        db_path = Path(__file__).parent / 'SEAM_common_drugs_supplements_choice_registry_v1.json'
        with open(db_path, 'r') as f:
            data = json.load(f)
        return data['compounds']
    except Exception as e:
        print(f"Error loading compounds: {e}")
        return []

# Load compounds at startup
COMPOUNDS = load_compounds()

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'lock_hash': LOCK_HASH,
        'rows': ROWS,
        'structures': STRUCTURES,
        'compounds_loaded': len(COMPOUNDS)
    })

@app.route('/compounds', methods=['GET'])
def get_compounds():
    """Get compound library"""
    return jsonify({
        'count': len(COMPOUNDS),
        'compounds': COMPOUNDS
    })

@app.route('/analyze', methods=['POST'])
def analyze():
    """Submit compounds for analysis"""
    global task_counter

    try:
        data = request.get_json()
        compounds = data.get('compounds', [])

        if not compounds:
            return jsonify({'error': 'No compounds provided'}), 400

        if len(compounds) > 50:
            return jsonify({'error': 'Maximum 50 compounds per analysis'}), 400

        # Create task
        task_counter += 1
        task_id = f"task_{task_counter}"

        task = {
            'id': task_id,
            'status': 'running',
            'progress': 0,
            'compounds': compounds,
            'result': None
        }
        tasks[task_id] = task

        # Start analysis in background
        thread = threading.Thread(
            target=run_analysis,
            args=(task_id, compounds),
            daemon=True
        )
        thread.start()

        return jsonify({
            'task_id': task_id,
            'status': 'running',
            'message': 'Analysis started'
        }), 202

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/results/<task_id>', methods=['GET'])
def get_results(task_id):
    """Get analysis results"""
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404

    task = tasks[task_id]
    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'result': task['result']
    })

def run_analysis(task_id, compounds):
    """Run analysis in background"""
    try:
        task = tasks[task_id]

        # Simulate analysis progress
        for i in range(0, 91, 10):
            task['progress'] = i
            time.sleep(0.2)

        # Generate results
        results = {
            'lock_sha256': LOCK_HASH,
            'rows': ROWS,
            'structures': STRUCTURES,
            'compounds_analyzed': len(compounds),
            'compounds': []
        }

        for compound in compounds:
            results['compounds'].append({
                'name': compound.get('generic_name'),
                'formula': compound.get('chemical_formula'),
                'category': compound.get('category'),
                'status': 'completed'
            })

        task['result'] = results
        task['status'] = 'completed'
        task['progress'] = 100

    except Exception as e:
        task = tasks[task_id]
        task['status'] = 'failed'
        task['error'] = str(e)

@app.route('/docs', methods=['GET'])
def docs():
    """API documentation"""
    return jsonify({
        'title': 'SEAM Compound Analyzer API',
        'endpoints': {
            'GET /health': 'Health check',
            'GET /compounds': 'Get 306-compound library',
            'POST /analyze': 'Submit for analysis',
            'GET /results/<task_id>': 'Get analysis results'
        }
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("  SEAM Compound Analyzer Backend")
    print("="*60)
    print(f"✓ Compounds loaded: {len(COMPOUNDS)}")
    print(f"✓ Lock: {LOCK_HASH[:16]}...")
    print(f"✓ Server starting on http://localhost:5000")
    print("="*60 + "\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
