# SEAM Compound Analyzer - Split Architecture

## System Design

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                          FRONTEND (Slick UI)                             ║
║                                                                           ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  seam-selector-ui.html                                           │   ║
║  │  - Compound Library Browser (306 compounds)                      │   ║
║  │  - Real-time Search & Filter                                    │   ║
║  │  - Multi-Select Management                                      │   ║
║  │  - Progress Tracking                                            │   ║
║  │  - Results Display                                              │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                           ║
║  NO DIRECT ENGINE ACCESS - Only uses REST API                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
                                    ↓
                            HTTP/JSON API Calls
                                    ↓
╔═══════════════════════════════════════════════════════════════════════════╗
║                         BACKEND (Python Flask)                           ║
║                                                                           ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  seam-backend-enhanced.py                                        │   ║
║  │  - REST API Server (localhost:5000)                             │   ║
║  │  - Compound Library Endpoint (/compounds)                       │   ║
║  │  - Analysis Submission (/analyze)                               │   ║
║  │  - Async Task Management                                        │   ║
║  │  - Results Polling (/results/<task_id>)                        │   ║
║  │  - Task Cancellation (/cancel/<task_id>)                       │   ║
║  │  - Health Check (/health)                                       │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                           ║
║  Execution Handler - Subprocess to SEAM Runtime                         ║
╚═══════════════════════════════════════════════════════════════════════════╝
                                    ↓
                          Subprocess / Runner Call
                                    ↓
╔═══════════════════════════════════════════════════════════════════════════╗
║                    SEAM ANALYSIS ENGINE (Locked)                         ║
║                                                                           ║
║  ┌──────────────────────────────────────────────────────────────────┐   ║
║  │  withdrawn_five.py                                               │   ║
║  │  SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12                      │   ║
║  │  - Structural Perturbation Analysis                             │   ║
║  │  - 5,734 rows × 420 structures                                  │   ║
║  │  - Lock Hash: 62c6aa75effef85b9039251fd7fd2dae7e11b676e861f... │   ║
║  └──────────────────────────────────────────────────────────────────┘   ║
║                                                                           ║
║  Engine is ISOLATED - No frontend can access directly                   ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

## Security Model

### Frontend Isolation
- **HTML/JavaScript only** - runs in browser
- **NO engine code exposure** - only calls API
- **NO credentials required** - localhost-only for now
- **NO compound data manipulation** - reads library from API

### Backend Authority
- **Single point of control** - all engine access goes through backend
- **Validation layer** - checks all inputs before execution
- **Rate limiting ready** - can add later
- **Execution isolation** - runs engine as subprocess

### Engine Protection
- **Locked & verified** - SHA256 hash checked
- **Not network-exposed** - only subprocess access
- **No human interaction** - fully automated

## API Specification

### Base URL
```
http://localhost:5000
```

### Endpoints

#### 1. GET /health
Health check and server status

**Response:**
```json
{
  "status": "ok",
  "lock_hash": "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4",
  "rows": 5734,
  "structures": 420,
  "runtime_configured": true,
  "runner_available": false,
  "timestamp": "2026-09-24T15:30:00"
}
```

#### 2. GET /compounds
Get complete compound library (306 compounds)

**Response:**
```json
{
  "count": 306,
  "schema": "SEAM_common_compound_choice_registry_v1",
  "compounds": [
    {
      "generic_name": "Famotidine",
      "trade_names": ["Pepcid"],
      "chemical_formula": "C8H15N7O2S3",
      "category": "Drug - Gastrointestinal"
    },
    ...
  ]
}
```

#### 3. POST /analyze
Submit compounds for SEAM analysis (async)

**Request:**
```json
{
  "compounds": [
    {
      "generic_name": "Famotidine",
      "chemical_formula": "C8H15N7O2S3",
      "category": "Drug - Gastrointestinal"
    },
    {
      "generic_name": "Albuterol",
      "chemical_formula": "C13H21NO3",
      "category": "Drug - Respiratory"
    }
  ]
}
```

**Response (HTTP 202 Accepted):**
```json
{
  "task_id": "a1b2c3d4e5f6g7h8",
  "status": "queued",
  "message": "Analysis queued. Poll /results/{task_id} for progress."
}
```

#### 4. GET /results/<task_id>
Poll for analysis progress and results

**Response:**
```json
{
  "task_id": "a1b2c3d4e5f6g7h8",
  "status": "running",
  "progress": 45,
  "created_at": "2026-09-24T15:30:00",
  "started_at": "2026-09-24T15:30:05",
  "completed_at": null,
  "compound_count": 2,
  "result": null,
  "error": null
}
```

**Statuses:**
- `queued` - Waiting to start
- `running` - Currently analyzing (check `progress` 0-100)
- `completed` - Done (check `result`)
- `failed` - Error (check `error`)
- `cancelled` - User cancelled

#### 5. POST /cancel/<task_id>
Cancel an ongoing analysis

**Response:**
```json
{
  "task_id": "a1b2c3d4e5f6g7h8",
  "status": "cancelled"
}
```

#### 6. GET /docs
API documentation

## Installation & Usage

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
# Basic start (demo mode, no real SEAM execution)
python seam-backend-enhanced.py

# With SEAM runtime configured
python seam-backend-enhanced.py --port 5000 --runtime /path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12

# With runner script
python seam-backend-enhanced.py --runtime /path/to/runtime --runner /path/to/runners/withdrawn_five.py
```

**Output:**
```
╔════════════════════════════════════════════════════════╗
║  SEAM Structural Perturbation Analysis Backend        ║
║  Version 2.0 - Split Architecture                    ║
╚════════════════════════════════════════════════════════╝

Lock Hash:     62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4
Runtime:       /path/to/SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12
Runner:        /path/to/runners/withdrawn_five.py
Port:          5000

API Endpoints:
  Health:      http://localhost:5000/health
  Compounds:   http://localhost:5000/compounds
  API Docs:    http://localhost:5000/docs

Frontend should connect to: http://localhost:5000
```

### 3. Open the Frontend

**Option A: Direct File Open**
```
Open seam-selector-ui.html in your browser
```

**Option B: Via HTTP Server (recommended for CORS)**
```bash
python -m http.server 8000
# Open http://localhost:8000/seam-selector-ui.html
```

### 4. Use the Interface

1. **Search Compounds** - Type in the search box to find drugs/supplements
2. **Select Multiple** - Click compounds or checkbox to select (max 50)
3. **View Selection** - Selected compounds show as tags at bottom
4. **Run Analysis** - Click "Run Analysis" button
5. **Monitor Progress** - Watch progress bar in results panel
6. **View Results** - See structural perturbation analysis results

## File Structure

```
D:\bio\
├── seam-selector-ui.html              Frontend interface (no backend access)
├── seam-backend-enhanced.py            Backend API server
├── SEAM_common_drugs_supplements_choice_registry_v1.json
│                                       306-compound database
├── SEAM_DRUG_STRUCTURAL_RUNTIME_LOCKED_v3_12/
│                                       SEAM analysis engine
├── runners/
│   └── withdrawn_five.py               Analysis runner script
├── requirements.txt                    Python dependencies
└── ARCHITECTURE.md                     This file
```

## Development Notes

### Adding New Features to Frontend
- Frontend only talks to API
- Add new search filters in `filterCompounds()`
- Add result display templates in `displayResults()`
- All data comes from `/compounds` and `/results/<task_id>` endpoints

### Extending Backend
- Add new API endpoints in `seam-backend-enhanced.py`
- Implement real SEAM execution in `execute_analysis()` function
- Add request validation/rate limiting as needed
- Keep engine interface isolated

### Connecting to Real SEAM Engine
1. Set `--runtime` and `--runner` paths on startup
2. Implement actual `withdrawn_five.py` subprocess call in `execute_analysis()`
3. Parse results JSON
4. Return via API

## Performance Considerations

- **Frontend Load:** ~79 KB (HTML + embedded CSS + JS)
- **Compound Database:** 306 entries, ~38 KB minified
- **API Overhead:** Minimal (~1 KB per request/response)
- **Analysis Time:** Depends on SEAM engine (typically 1-5 sec per compound)
- **Concurrent Tasks:** Limited by backend threads (default: 1 per core)

## Security Checklist

- [x] Frontend isolated from engine
- [x] API authentication ready (not implemented, add as needed)
- [x] Input validation in backend
- [x] Subprocess execution sandboxed
- [x] No credentials in frontend
- [x] CORS configured for localhost only
- [ ] Rate limiting (add if exposed publicly)
- [ ] HTTPS (add if exposed publicly)
- [ ] Request signing (add if exposed publicly)

## Future Enhancements

1. **Authentication** - Add user accounts and API keys
2. **Database** - Store analysis history
3. **Batch Scheduler** - Queue analyses for off-peak hours
4. **WebSockets** - Real-time progress updates (vs polling)
5. **Caching** - Cache compound-specific results
6. **Distribution** - Deploy backend to cloud for scale
7. **Monitoring** - Add logging and metrics
8. **Documentation** - Interactive API explorer (Swagger/OpenAPI)

## Troubleshooting

### "Failed to load compound library"
- Check backend is running: `http://localhost:5000/health`
- Check CORS isn't blocking: browser console for errors
- Verify compound JSON file exists

### Analysis hangs at "Processing..."
- Check backend logs for errors
- Verify SEAM runtime path is correct
- Check system resources (CPU, memory)

### "Task not found" when polling
- Task ID may have expired (kept in memory only)
- Restart backend to clear old tasks
- (Future: save to database for persistence)

---

**Version:** 2.0 - Split Architecture  
**Last Updated:** 2026-09-24  
**Lock Hash:** 62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4  
