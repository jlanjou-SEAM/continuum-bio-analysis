# Deployment Checklist

Complete this checklist to verify your SEAM analyzer is ready for production.

## Files & Structure

### Source Code
- [ ] `seam-server-enhanced.c` exists (main C server, loads 306 compounds)
- [ ] `seam-server.c` exists (optional minimal version)
- [ ] `seam-ui-improved.html` exists (frontend)
- [ ] `SEAM_common_drugs_supplements_choice_registry_v1.json` exists (306 compounds)

### Build Scripts
- [ ] `BUILD.sh` exists and is executable (`chmod +x BUILD.sh`)
- [ ] `BUILD.bat` exists (Windows)

### Documentation
- [ ] `README_C_BACKEND.md` (main overview)
- [ ] `SEAM_C_SERVER_README.md` (API reference)
- [ ] `QUICKSTART_C.md` (3-minute start)
- [ ] `DEPLOY_SETUP.md` (deployment guide)
- [ ] `MIGRATION_PYTHON_TO_C.md` (Python migration)

## Environment Setup

### Linux / macOS
- [ ] GCC installed: `gcc --version` works
- [ ] pthreads available (standard on Unix)
- [ ] Working directory has all files above

### Windows
- [ ] MinGW installed OR WSL enabled
- [ ] GCC accessible from command line
- [ ] File paths use backslashes or forward slashes

## Build Verification

### Build Enhanced Version
- [ ] Run: `./BUILD.sh enhanced` (Unix) or `BUILD.bat enhanced` (Windows)
- [ ] Build succeeds (no errors)
- [ ] Binary created: `seam-server` or `seam-server.exe` (~200-300 KB)

### Build Minimal Version (Optional)
- [ ] Run: `./BUILD.sh minimal`
- [ ] Binary created: `seam-server-minimal` (~180 KB)

### Build Test
```bash
# Should show executable
file seam-server
# or
ls -lh seam-server
```
- [ ] Binary is executable
- [ ] Size ~200-300 KB

## Runtime Testing

### Start Server
```bash
./seam-server
```
- [ ] Output shows:
  - `✓ Lock: 62c6aa75...`
  - `✓ Server starting on http://localhost:5000`
  - `✓ Database: 306 compounds loaded`
- [ ] No errors in output
- [ ] Server keeps running (doesn't exit)

### Test /health Endpoint
```bash
curl http://localhost:5000/health
```
- [ ] Returns JSON with `"status": "ok"`
- [ ] Shows lock hash: `62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4`
- [ ] Shows 306 compounds
- [ ] Shows 5734 rows, 420 structures

### Test /compounds Endpoint
```bash
curl http://localhost:5000/compounds | jq '.count'
```
- [ ] Returns `306`
- [ ] Response includes compound names, formulas, categories
- [ ] Can find "Famotidine", "Ibuprofen", "Acetaminophen"

### Test /analyze Endpoint
```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"compounds": ["Famotidine"]}'
```
- [ ] Returns 202 status code
- [ ] Includes `"task_id": "task_1"`
- [ ] Shows `"status": "running"`

### Test /results Endpoint
```bash
curl http://localhost:5000/results/task_1
```
- [ ] Returns task status
- [ ] Progress increases (0 → 100)
- [ ] Eventually shows completed with results

### Test CORS
```bash
curl -X OPTIONS http://localhost:5000/analyze \
  -H "Origin: http://localhost:3000"
```
- [ ] Returns 200 status
- [ ] Includes `Access-Control-Allow-Origin: *`
- [ ] Includes `Access-Control-Allow-Methods: GET, POST, OPTIONS`

## Frontend Testing

### Local File (file://)
- [ ] Open `seam-ui-improved.html` directly in browser
- [ ] Note: CORS may not work with `file://` protocol
- [ ] Expect error: "Failed to fetch"

### Via HTTP Server
```bash
# Terminal 1: Start C server
./seam-server

# Terminal 2: Start HTTP server (choose one)
python3 -m http.server 8080
# or
npx http-server
# or
php -S localhost:8080
```

Then open: `http://localhost:8080/seam-ui-improved.html`

- [ ] Page loads without CORS errors
- [ ] Compound selector modal works
- [ ] Can search compounds (e.g., "Famot")
- [ ] Can select checkboxes
- [ ] Can click "Analyze" button
- [ ] Progress bar appears
- [ ] Results display after completion

## Data Validation

### Verify Lock Hash
```bash
grep "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4" seam-server-enhanced.c
```
- [ ] Hash found in C source

### Verify Compound Count
```bash
jq '.count' SEAM_common_drugs_supplements_choice_registry_v1.json
```
- [ ] Returns `306`

### Verify Database Format
```bash
jq '.compounds[0]' SEAM_common_drugs_supplements_choice_registry_v1.json
```
- [ ] Includes: `generic_name`, `chemical_formula`, `category`, `trade_names`

## Deployment

### Docker (Optional)
- [ ] Dockerfile created or exists
- [ ] Build works: `docker build -t seam-analyzer .`
- [ ] Container runs: `docker run -p 5000:5000 seam-analyzer`
- [ ] `/health` accessible from host

### Systemd (Linux, Optional)
- [ ] Service file created at `/etc/systemd/system/seam-analyzer.service`
- [ ] Can enable: `sudo systemctl enable seam-analyzer`
- [ ] Can start: `sudo systemctl start seam-analyzer`
- [ ] Can check status: `sudo systemctl status seam-analyzer`

### Kubernetes (Optional)
- [ ] YAML deployment created
- [ ] Can apply: `kubectl apply -f seam-deployment.yaml`
- [ ] Pods running: `kubectl get pods`

## CI/CD Integration

### GitHub Actions (Optional)
- [ ] `.github/workflows/build.yml` created
- [ ] Triggers on push
- [ ] Compiles C binary
- [ ] Uploads artifact

### GitLab CI (Optional)
- [ ] `.gitlab-ci.yml` created
- [ ] `build` stage compiles
- [ ] `deploy` stage pushes to registry

## Performance

### Startup Time
```bash
time ./seam-server
```
- [ ] Takes < 100 ms to start and bind port
- [ ] Loads 306 compounds in < 100 ms

### Request Latency
```bash
for i in {1..10}; do curl -w "%{time_total}s\n" http://localhost:5000/health; done
```
- [ ] Most requests < 5 ms
- [ ] No requests > 100 ms

### Memory Usage
```bash
ps aux | grep seam-server
```
- [ ] RSS ~2-5 MB at idle
- [ ] RSS doesn't grow unbounded with requests

## Security

### Localhost Only
```bash
netstat -tulnp | grep 5000
```
- [ ] Shows `127.0.0.1:5000` (not `0.0.0.0:5000`)
- [ ] Or `LISTEN` on loopback only

### No Dependencies
```bash
ldd seam-server
```
- [ ] Shows only standard libraries (libc, libpthread)
- [ ] No Flask, no external deps

### Port Binding
- [ ] Fails gracefully if port 5000 in use
- [ ] Can change port in source and rebuild
- [ ] Restart doesn't hang or crash

## Maintenance

### Restart Procedure
1. [ ] Can stop server gracefully: `Ctrl+C`
2. [ ] Can find process: `lsof -i :5000`
3. [ ] Can kill forcefully: `kill -9 <PID>`
4. [ ] Can restart without conflicts: `./seam-server`

### Database Updates
1. [ ] Edit `SEAM_common_drugs_supplements_choice_registry_v1.json`
2. [ ] Restart server: `kill -9 $(lsof -t -i :5000); ./seam-server`
3. [ ] Test /compounds returns new data
4. [ ] **Note:** No rebuild needed

### Log Rotation (if deployed)
- [ ] Logs sent to stdout (capture with redirection)
- [ ] Example: `./seam-server >> /var/log/seam.log 2>&1 &`
- [ ] Configure logrotate or similar if needed

## Documentation Review

- [ ] All README files are accurate
- [ ] No broken links
- [ ] All commands tested
- [ ] Port 5000 mentioned consistently (or changed if customized)
- [ ] Lock hash verified in multiple places

## Production Readiness

### Code Quality
- [ ] No compiler warnings: `gcc -Wall -Wextra seam-server-enhanced.c`
- [ ] CORS headers present
- [ ] Error handling for file not found
- [ ] Graceful degradation (falls back to 5 demo compounds)

### Reliability
- [ ] Server doesn't crash on malformed requests
- [ ] Server handles 100+ concurrent connections
- [ ] Task cleanup doesn't leak memory
- [ ] Restarts cleanly after crashes

### Completeness
- [ ] All endpoints implemented: /health, /compounds, /analyze, /results
- [ ] All required response fields present
- [ ] All documented fields working correctly

## Go/No-Go Decision

**All items checked?** ✓ **READY FOR PRODUCTION**

**If not:**
1. Review unchecked items
2. See relevant documentation (README_C_BACKEND.md, SEAM_C_SERVER_README.md, DEPLOY_SETUP.md)
3. Fix issues
4. Recheck

## Deployment Sign-Off

- **Checked by:** ___________________
- **Date:** ___________________
- **Production URL:** ___________________
- **Notes:** ___________________

---

**Next Steps:**
1. Complete checklist above
2. Deploy using DEPLOY_SETUP.md
3. Monitor with health endpoint: `curl http://localhost:5000/health`
4. Keep documentation current
