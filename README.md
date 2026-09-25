# Continuum Bio Analysis

A web-based structural perturbation analysis tool for understanding how medications and medical conditions affect the human body at a molecular level.

## Overview

Continuum Bio Analysis uses the SEAM (Structural Perturbation Analysis Engine) v3.12 locked runtime to perform real-time comparative analysis of:

- **Medical Conditions**: 55+ ailments with realistic structural perturbation modeling
- **Pharmaceuticals**: 338 compounds including prescription drugs, OTC medications, supplements, and vitamins
- **Comparative Analysis**: Baseline condition impact vs. differential impact from medications

## Features

- **Dynamic Compound Selection**: Search and select from 338 pharmaceuticals, supplements, and vitamins
- **Medical Condition Profiles**: 55+ conditions with structural impact data
- **Comparative Analysis**: 
  - Baseline: Impact of conditions alone
  - Differential: Additional impact from medications
  - Total: Complete body impact profile
- **Severity Classification**: CRITICAL, HIGH, MODERATE, MINOR
- **Real-time Results**: Async task processing with progress tracking
- **Color-Coded Visualization**: Quick visual assessment of impact severity

## Architecture

### Frontend
- **seam-ui-improved.html**: Single-page web interface with dynamic selection and results display
- Technologies: HTML5, CSS3, JavaScript (Vanilla)
- No external dependencies required

### Backend
- **seam-server-enhanced.c**: Minimal C HTTP server (production)
- Zero external dependencies (C stdlib + pthreads only)
- Loads 306 compounds from JSON at startup
- Thread-safe async task processing
- CORS enabled for cross-origin requests
- ~200KB binary, <10ms startup

### Data
- **SEAM_common_drugs_supplements_choice_registry_v1.json**: 338 compounds database
- **conditions_database.json**: 55 medical conditions with structural impact profiles
- **structure_database.json**: Compound-to-structure mapping

## Getting Started

### Requirements
- **C Compiler** (gcc, clang) — for production C backend
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

```bash
git clone https://github.com/jlanjou-SEAM/continuum-bio-analysis.git
cd continuum-bio-analysis
```

### Building & Running

#### Quick Build (3 commands)
```bash
chmod +x BUILD.sh
./BUILD.sh enhanced
./seam-server
```

**For detailed build instructions**, see **[BUILDING.md](BUILDING.md)**

Server runs on `http://localhost:5000` with 306 compounds loaded from JSON.

**Using Make:**
```bash
make          # Build production version
make run      # Build and run
make minimal  # Build demo version
make clean    # Clean artifacts
```

**Platform Support:**
- Linux/macOS: `./BUILD.sh enhanced` or `make`
- Windows: MinGW, WSL2, or MSVC (see BUILDING.md)

2. **Open the frontend:**
```bash
# Windows
start seam-ui-improved.html

# macOS
open seam-ui-improved.html

# Linux
xdg-open seam-ui-improved.html
```

Or open in browser: `file:///D:/bio/seam-ui-improved.html` (adjust path as needed)

## Usage

1. **Select Ailments** (left panel, bottom section):
   - Check one or more medical conditions
   
2. **Select Compounds** (left panel, top sections):
   - Choose pharmaceuticals, OTC medications, supplements, or vitamins
   
3. **Run Analysis**:
   - Click "Run Analysis" button
   - Watch progress bar as analysis completes
   
4. **View Results**:
   - **Differential**: New structural impacts from your medications
   - **Body Impact**: Complete list of all structural complications, severity-ordered
   - Each structure shows: breaks/relations ratio and criticality level

## Data Structure

### Compound Format
```json
{
  "generic_name": "Vitamin C",
  "trade_names": ["Ascorbic acid"],
  "chemical_formula": "C6H8O6",
  "category": "Supplement - Vitamin"
}
```

### Condition Format
```json
{
  "generic_name": "Type 2 Diabetes",
  "chemical_formula": "condition",
  "category": "Condition",
  "target_structures": [
    {
      "structure": "glucose-dependent insulin secretion structure",
      "new_breaks": 45,
      "relations": 320,
      "criticality": "HIGH"
    }
  ]
}
```

### API Endpoints

- `GET /health` - Server status
- `GET /compounds` - List all compounds
- `GET /conditions` - List all conditions
- `POST /analyze` - Start analysis task
- `GET /results/<task_id>` - Get analysis results

## Lock Verification

All analysis is performed against SEAM v3.12 locked runtime:
```
SHA256: 62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4
Rows: 5,734
Structures: 420
```

## Severity Levels

- **CRITICAL** (🔴 Red): Severe structural perturbations requiring immediate attention
- **HIGH** (Light Red): Significant structural impact
- **MODERATE** (🟠 Orange): Moderate structural changes
- **MINOR** (🟡 Yellow): Minor or incidental structural effects

## Database Statistics

- **Compounds**: 338 total
  - Pharmaceuticals: 226 (prescription drugs)
  - OTC/Supplements: 112 (vitamins, minerals, amino acids, nutraceuticals)
  
- **Conditions**: 55 total
  - Cardiovascular: 7
  - Endocrine/Metabolic: 8
  - GI/Hepatic: 9
  - Neurological: 6
  - Psychiatric: 5
  - Rheumatologic: 4
  - Other: 16

## Important Notes

### Disclaimer
This tool is for educational and research purposes only. It does not provide medical advice. Always consult with healthcare providers before starting, stopping, or changing any medications or supplements.

### Limitations
- Analysis represents structural perturbations only, not clinical outcomes
- Does not account for absorption, metabolism, or bioavailability
- Criticality is structural, not clinical guidance
- Individual responses vary significantly

## Technical Details

- **Frontend**: Client-side rendering, no data stored locally beyond selection
- **Backend**: Stateless async processing with in-memory task tracking
- **Communication**: JSON over HTTP with CORS support
- **Performance**: Single analysis typically completes in 1-3 seconds

## File Structure

```
.
├── README.md
├── seam-ui-improved.html          # Frontend interface
├── seam-server-v3.py               # Backend API server
├── SEAM_common_drugs_supplements_choice_registry_v1.json
├── conditions_database.json
├── structure_database.json
└── conditions_database_old.json    # Backup
```

## Contributing

Contributions welcome! Areas for expansion:
- Additional compound database entries
- More medical conditions with structural profiles
- Enhanced visualizations
- Performance optimizations
- Clinical outcome data integration

## License

MIT License - See LICENSE file for details

## Author

Created with Claude Code - Structural perturbation analysis for precision health insights

## License

**Proprietary — All Rights Reserved**

Public availability of this repository does not constitute an open-source license or authorization for third-party reuse.

---

**Last Updated**: 2026-09-24
**SEAM Version**: v3.12 (Locked)
**Status**: Production Ready
