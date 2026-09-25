# SEAM Dynamic Compound Analyzer - Setup Guide

## Overview

The SEAM Dynamic Compound Analyzer is an interactive web application that allows you to:

1. **Select compounds** from a comprehensive database (60+ drugs, OTC meds, supplements)
2. **Multi-select** to analyze multiple compounds at once
3. **Run real-time SEAM analysis** showing structural perturbation results
4. **View structural responses** in individual compound profiles

## Architecture

```
┌─────────────────────┐
│  Browser / HTML UI  │  ← seam-dynamic.html
│  - Compound Select  │     (Popup modal with checkboxes)
│  - Results Display  │
└──────────┬──────────┘
           │ HTTP POST /analyze
           ▼
┌─────────────────────┐
│  Python Flask API   │  ← seam-backend.py
│  - Request Handler  │     (REST API server)
│  - SEAM Runner      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SEAM Runtime       │  ← SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12
│  (v3.12 Locked)     │     (Binary runtime, 5,734 rows × 420 structures)
└─────────────────────┘

Data Flow:
drug_compounds.json → HTML Selector → Flask API → SEAM Runtime → Results JSON → Display
```

## Files

- **seam-dynamic.html** — Interactive web interface with:
  - Popup/modal compound selector (columnated checkbox list)
  - Selected compounds shown as collapsible tags
  - Results display section
  - Real-time filtering/search

- **seam-backend.py** — Flask REST API that:
  - Accepts POST requests with selected compounds
  - Validates against the locked runtime
  - Executes SEAM analysis
  - Returns JSON results

- **drug_compounds.json** — Comprehensive database with:
  - 60+ compounds (drugs, OTC meds, supplements)
  - Chemical formulas and molecular weights
  - Typical doses and categories
  - Status (marketed, OTC, Rx, withdrawn)

- **requirements.txt** — Python dependencies

## Installation

### Prerequisites

- Python 3.7+
- Modern web browser
- SEAM runtime: `SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12` (extracted from archives)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Verify Runtime Path

The backend needs the SEAM runtime. You can provide it via:

```bash
# Option A: Command line argument
python seam-backend.py --runtime /path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12

# Option B: Update RUNTIME_PATH in seam-backend.py
# Edit seam-backend.py and set RUNTIME_PATH = "/path/to/runtime"

# Option C: Set environment variable
set SEAM_RUNTIME_PATH=/path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12
```

### Step 3: Start the Backend Server

```bash
python seam-backend.py --port 5000
```

Expected output:
```
Starting SEAM Analysis Backend Server
Lock: 62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4
Runtime: /path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12
Port: 5000

Open in browser: http://localhost:5000
API docs: http://localhost:5000/docs
```

### Step 4: Open the Web Interface

Open **seam-dynamic.html** in your browser (same directory as the backend):

```
file:///path/to/bio/seam-dynamic.html
```

Or navigate to:
```
http://localhost:5000/static/seam-dynamic.html
```

## Usage

### Single Compound Analysis

1. Click **+ Add Compounds**
2. Search for a compound (e.g., "famotidine")
3. Check the checkbox
4. Click **Close**
5. Click **Run Analysis**

### Multi-Compound Analysis (Batch)

1. Click **+ Add Compounds**
2. Search and select multiple compounds:
   - Check "famotidine"
   - Check "albuterol"
   - Check "caffeine"
3. Click **Close** (selected compounds show as tags)
4. Click **Run Analysis**

Results display:
- Control transitions (λ=0)
- Rows with new breaks
- Criticality tier distribution
- Top target structures
- Known clinical profile

### Selection Management

- **Remove one**: Click **×** on any compound tag
- **Clear all**: Click **Clear All** button
- **Search**: Use search box in popup to filter by:
  - Name (e.g., "fluoxetine")
  - Formula (e.g., "C8H")
  - Category (e.g., "antibiotic", "supplement")
  - Status (e.g., "withdrawn", "OTC")

## API Endpoints

### GET /health
Health check and configuration status.

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "ok",
  "lock_hash": "62c6aa75...",
  "rows": 5734,
  "structures": 420,
  "runtime_configured": true
}
```

### GET /compounds
Get the compound library.

```bash
curl http://localhost:5000/compounds
```

### POST /analyze
Run SEAM analysis on selected compounds.

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "compounds": [
      {
        "name": "famotidine",
        "formula": "C8H15N7O2S3",
        "mw": 337.445,
        "dose_mg_day": 40
      }
    ],
    "runtime_path": "/path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12"
  }'
```

### GET /docs
API documentation.

```bash
curl http://localhost:5000/docs
```

## Compound Database

The `drug_compounds.json` database includes:

### Categories
- **Analgesics/Antipyretics**: acetaminophen, aspirin
- **NSAIDs**: ibuprofen, naproxen, rofecoxib
- **Antihistamines**: diphenhydramine, loratadine, cetirizine, terfenadine
- **Antacids/H2 Blockers**: omeprazole, famotidine, ranitidine
- **Cardiovascular**: lisinopril, metoprolol, amlodipine, simvastatin
- **Antidiabetic**: metformin
- **Thyroid**: levothyroxine
- **Respiratory**: albuterol
- **Psychiatric**: sertraline, fluoxetine, amitriptyline
- **Supplements**: vitamin C/D/B12, folic acid, iron, magnesium, calcium
- **Herbal**: ginger, turmeric, garlic, echinacea, valerian
- **Antibiotics**: amoxicillin, erythromycin
- **Antifungal**: ketoconazole, fluconazole
- **Anticoagulant**: warfarin

### Status Labels
- **OTC** — Over-the-counter
- **Rx** — Prescription
- **Withdrawn** — No longer marketed (historical analysis)
- **OTC/Rx** — Available both ways

## Runtime Requirements

The backend requires the SEAM v3.12 locked runtime:

```
SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12/
├── data/
│   ├── prescreen.lock
│   └── [5,734 rows × 420 structures]
├── runners/
│   └── withdrawn_five.py
└── results/
    └── [analysis outputs]
```

**Lock Hash:** `62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4`

To extract from the archives:
```bash
# Extract from SEAM_Famotidine_Ammonia_Perturbation_Engineering_Archive_v1.zip
unzip SEAM_Famotidine_Ammonia_Perturbation_Engineering_Archive_v1.zip

# The runtime is inside the extracted directory
```

## Troubleshooting

### "Server is not running"

The frontend is trying to connect to `http://localhost:5000` but the backend isn't started.

**Fix:**
```bash
python seam-backend.py --runtime /path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12
```

### "Runtime not configured or not found"

The backend doesn't have the SEAM runtime path set.

**Fix:**
```bash
# Pass it on command line
python seam-backend.py --runtime /path/to/runtime

# OR edit seam-backend.py and set RUNTIME_PATH variable
# OR provide it in the analysis request
```

### CORS errors in browser console

The frontend HTML file is loaded as `file://` protocol, which has CORS restrictions.

**Fix:**
```bash
# Start a simple HTTP server in the directory
python -m http.server 8000

# Then open http://localhost:8000/seam-dynamic.html
```

### "ModuleNotFoundError: No module named 'flask'"

Dependencies not installed.

**Fix:**
```bash
pip install -r requirements.txt
```

## Development

### Adding a New Compound

Edit `drug_compounds.json` and add an entry:

```json
{
  "name": "new-drug",
  "formula": "C12H22O11",
  "mw": 342.296,
  "category": "category-name",
  "typical_dose_mg": 100,
  "status": "Rx"
}
```

### Adding a New Analysis Feature

Edit `seam-backend.py`:

```python
@app.route('/new-endpoint', methods=['POST'])
def new_endpoint():
    # Your logic here
    return jsonify({'result': 'data'})
```

Rebuild frontend in `seam-dynamic.html` to call:
```javascript
fetch('http://localhost:5000/new-endpoint', {
    method: 'POST',
    body: JSON.stringify({...})
})
```

## Performance Notes

- **Compound selection:** Instant
- **Multi-select:** No limit on number of compounds
- **Analysis latency:** Depends on SEAM runtime performance
  - Single compound: ~1-2 seconds (varies by compound complexity)
  - Batch (5 compounds): ~5-10 seconds
  - Large batch (20+ compounds): ~30+ seconds

## Security Notes

- **Lock verification:** Every request verifies against the hardcoded lock hash
- **Runtime validation:** Backend checks runtime path exists and validates structure
- **CORS enabled:** Frontend can only communicate with `localhost:5000`
- **Input validation:** All compound inputs validated against the library
- **No persistence:** Results are not saved; each analysis is independent

## Citation

If you use this interface in research or clinical work, cite:

```
SEAM Structural Perturbation Analysis
Lock: 62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4
Runtime: SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12
Rows: 5,734 | Structures: 420
```

## Support

For issues or questions:
1. Check `/docs` endpoint for API specification
2. Review `MANIFEST.md` for known limitations
3. Verify runtime path and lock hash
4. Check browser console for error messages
