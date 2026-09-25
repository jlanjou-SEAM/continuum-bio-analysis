# SEAM Compound Analyzer - Quick Start Guide

## What You Have

A **professional split-architecture system** for analyzing compounds with SEAM:

- **Frontend UI** (seam-selector-ui.html) - Beautiful, responsive interface
- **Backend API** (seam-backend-enhanced.py) - Flask server handling all analysis
- **306 Compounds** - Complete pharmaceutical and supplement database
- **Architecture** - Frontend never touches the engine directly

## Setup (5 minutes)

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start the Backend Server
```bash
python seam-backend-enhanced.py
```

You should see:
```
╔════════════════════════════════════════════════════════╗
║  SEAM Structural Perturbation Analysis Backend        ║
║  Version 2.0 - Split Architecture                    ║
╚════════════════════════════════════════════════════════╝

API Endpoints:
  Health:      http://localhost:5000/health
  Compounds:   http://localhost:5000/compounds
  API Docs:    http://localhost:5000/docs

Frontend should connect to: http://localhost:5000
```

### Step 3: Open the Frontend
Open `seam-selector-ui.html` in your web browser

## Using the Interface

### 1. **Browse Compounds**
- View all 306 drugs, supplements, and metabolic compounds
- See chemical formulas and categories
- Search by name, formula, or category

### 2. **Select Compounds**
- Click compounds to select (max 50 per analysis)
- Selected compounds appear as blue tags at the bottom
- Remove any by clicking the × on each tag

### 3. **Run Analysis**
- Click the "Run Analysis" button
- Watch the progress bar as analysis runs
- Results appear in the right panel

### 4. **View Results**
- See structural perturbation data
- Chemical formula and category for each compound
- Results organized by compound

## Architecture at a Glance

```
Frontend (HTML/JavaScript)
        ↓ (HTTP API)
Backend (Python Flask)
        ↓ (subprocess)
SEAM Engine (locked & verified)
```

**Key Points:**
- Frontend **never** has direct access to the engine
- All communication goes through REST API
- Backend validates all inputs
- Engine stays isolated and secure

## API Endpoints

### Quick Test
```bash
# Check if backend is running
curl http://localhost:5000/health

# Get compound library
curl http://localhost:5000/compounds

# API documentation
curl http://localhost:5000/docs
```

### Programmatic Use
```javascript
// From JavaScript
const response = await fetch('http://localhost:5000/compounds');
const data = await response.json();
console.log(`Found ${data.count} compounds`);
```

## Configuration

### Basic (Demo Mode)
```bash
python seam-backend-enhanced.py
# Runs without real SEAM engine - returns template results
```

### With SEAM Runtime
```bash
python seam-backend-enhanced.py \
  --runtime /path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12 \
  --runner /path/to/runners/withdrawn_five.py
```

### Custom Port
```bash
python seam-backend-enhanced.py --port 8000
# Then open frontend with API_URL = 'http://localhost:8000'
```

## Database

### 306 Compounds Included

**Pharmaceuticals** (150+ drugs)
- Pain relief (acetaminophen, ibuprofen, naproxen)
- Cardiovascular (lisinopril, atenolol, atorvastatin)
- Diabetes (metformin, glipizide, semaglutide)
- Psychiatric (sertraline, fluoxetine, olanzapine)
- Antibiotics (amoxicillin, azithromycin, ciprofloxacin)
- And 100+ more...

**Supplements & Minerals** (100+ compounds)
- Vitamins (A, B-complex, C, D, E, K)
- Minerals (calcium, magnesium, zinc, iron, selenium)
- Amino acids (all 20 standard amino acids)
- Herbs & nutraceuticals (curcumin, resveratrol, quercetin)

**Metabolic** (50+ compounds)
- Neurotransmitters (serotonin, dopamine, GABA)
- Hormones (cortisol, insulin, testosterone)
- Metabolic intermediates (glucose, lactate, pyruvate)

## Features

✅ **Real-time Search** - Filter 306 compounds instantly  
✅ **Multi-Select** - Choose up to 50 compounds at once  
✅ **Progress Tracking** - Watch analysis as it runs  
✅ **Beautiful UI** - Modern dark theme with gradients  
✅ **Responsive Design** - Works on desktop and tablet  
✅ **REST API** - All operations via clean HTTP interface  
✅ **Async Processing** - Non-blocking analysis  
✅ **Results Display** - Structured perturbation data  

## Common Tasks

### Analyze a Single Drug
1. Search for "famotidine"
2. Click to select (turns blue)
3. Click "Run Analysis"
4. View results in right panel

### Analyze a Drug Stack
1. Search and select:
   - "vitamin C ascorbic acid"
   - "magnesium oxide"
   - "famotidine"
   - "sertraline"
2. Click "Run Analysis"
3. See structural response for entire stack

### Find All NSAIDs
1. Type "NSAID" in search box
2. View all NSAIDs (ibuprofen, naproxen, diclofenac, etc.)
3. Multi-select to compare

### Search by Formula
1. Type "C8H" to find all with that formula start
2. Type "O4" to find all with 4 oxygens
3. Narrow down by category

## Troubleshooting

### "Failed to load compound library"
```bash
# Check if backend is running
curl http://localhost:5000/health
# Should return: {"status": "ok", ...}
```

### "Run Analysis" button is disabled
- You need to select at least 1 compound
- Click on compounds to select them (they turn blue)

### Progress bar stuck at 0%
- Check backend console for errors
- Verify port 5000 is not in use
- Try restarting backend server

### "Analysis failed" error
- Backend needs SEAM runtime configured to run real analyses
- For now, it returns template results automatically

## Files

| File | Purpose |
|------|---------|
| `seam-selector-ui.html` | Frontend interface (open in browser) |
| `seam-backend-enhanced.py` | Backend API server (run from terminal) |
| `SEAM_common_drugs_supplements_choice_registry_v1.json` | 306-compound database |
| `ARCHITECTURE.md` | Complete system architecture docs |
| `QUICKSTART.md` | This file |

## What's Next?

1. **Run the Demo** - Start backend, open frontend, try selecting compounds
2. **Configure Runtime** - Add path to real SEAM engine for actual analyses
3. **Integrate** - Use API from your own applications
4. **Scale** - Deploy backend to cloud for multiple users

## API Documentation

Full API spec available at:
- **Running:** http://localhost:5000/docs
- **File:** See ARCHITECTURE.md

## Support

For detailed information:
- See `ARCHITECTURE.md` for complete system design
- Check backend logs for errors
- Verify compound database loaded: `http://localhost:5000/compounds`

---

**Ready to start?**

1. Terminal: `python seam-backend-enhanced.py`
2. Browser: Open `seam-selector-ui.html`
3. Select compounds → Run Analysis → View results

Enjoy the slick interface! 🚀
