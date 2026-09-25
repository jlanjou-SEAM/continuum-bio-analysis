# SEAM C Server — Minimal Implementation

A **zero-dependency C HTTP server** for the SEAM compound analyzer. Compiles to a single binary, perfect for locked CI/CD environments.

## Why C?

- **No runtime dependency**: Just compile and run
- **Reproducible**: Same binary every push
- **Fast**: Native performance
- **Portable**: Runs on Linux, macOS, Windows (MinGW)
- **Locked environments**: Works in restricted CI/CD without package managers

## Lock Verification

```
Lock SHA256: 62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4
Rows:       5,734
Structures: 420
```

The lock hash is **hardcoded** in the binary. No configuration needed.

## Building

### macOS / Linux

```bash
chmod +x BUILD.sh
./BUILD.sh
```

### Windows (MinGW)

```cmd
BUILD.bat
```

Or manually:
```bash
gcc -o seam-server.exe seam-server.c -lpthread -Wall -Wextra -O2
```

### Docker (Optional)

```dockerfile
FROM gcc:latest
WORKDIR /app
COPY seam-server.c .
RUN gcc -o seam-server seam-server.c -lpthread -O2
EXPOSE 5000
CMD ["./seam-server"]
```

## Running

### Local

```bash
./seam-server
# Listen on http://localhost:5000
```

### Background (Linux/macOS)

```bash
./seam-server &
```

### Docker

```bash
docker build -t seam-server .
docker run -p 5000:5000 seam-server
```

## API Endpoints

### GET /health

Verify server is running and show lock info.

```bash
curl http://localhost:5000/health
```

Response:
```json
{
  "status": "ok",
  "lock_hash": "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4",
  "rows": 5734,
  "structures": 420,
  "compounds": 5
}
```

### GET /compounds

List all available compounds.

```bash
curl http://localhost:5000/compounds
```

Response:
```json
{
  "count": 5,
  "compounds": [
    {
      "generic_name": "Acetaminophen",
      "chemical_formula": "C8H9NO2",
      "category": "Drug - Pain/fever",
      "trade_names": []
    },
    ...
  ]
}
```

### POST /analyze

Submit compounds for analysis (returns task ID for polling).

```bash
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"compounds": ["Famotidine", "Acetaminophen"]}'
```

Response:
```json
{
  "task_id": "task_1",
  "status": "running"
}
```

### GET /results/{task_id}

Poll analysis progress.

```bash
curl http://localhost:5000/results/task_1
```

Response:
```json
{
  "task_id": "task_1",
  "status": "running",
  "progress": 50,
  "result": null
}
```

When complete:
```json
{
  "task_id": "task_1",
  "status": "completed",
  "progress": 100,
  "result": {
    "lock_sha256": "62c6aa75...",
    "rows": 5734,
    "structures": 420,
    "compounds_analyzed": 2,
    "compounds": [...]
  }
}
```

## CORS Support

All endpoints return CORS headers for cross-origin requests:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET, POST, OPTIONS`
- `Access-Control-Allow-Headers: Content-Type`

## Frontend Integration

The server works with **seam-ui-improved.html**:

```html
<!-- Open UI in browser -->
<script>
  const baseURL = 'http://localhost:5000';
  
  // Fetch available compounds
  fetch(`${baseURL}/compounds`)
    .then(r => r.json())
    .then(data => console.log(data.compounds));
  
  // Submit analysis
  fetch(`${baseURL}/analyze`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({compounds: ['Famotidine', 'Ibuprofen']})
  })
    .then(r => r.json())
    .then(task => console.log(task.task_id));
</script>
```

## Limitations & Future Work

### Current (v1.0)

- ✓ Hardcoded 5 compounds (demo)
- ✓ Simulated analysis (200ms per progress step)
- ✓ HTTP server with CORS
- ✓ Async task tracking with threading

### To Add

- [ ] Load 306-compound database from JSON at startup
- [ ] Invoke actual SEAM engine subprocess
- [ ] Robust JSON parsing for POST body
- [ ] Request validation
- [ ] Per-compound result caching
- [ ] Graceful shutdown handler (SIGTERM)
- [ ] Access logging

## CI/CD Integration

### GitHub Actions

```yaml
jobs:
  seam-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build SEAM server
        run: ./BUILD.sh
      - name: Upload binary
        uses: actions/upload-artifact@v3
        with:
          name: seam-server
          path: seam-server
```

### GitLab CI

```yaml
build-seam-server:
  stage: build
  image: gcc:latest
  script:
    - gcc -o seam-server seam-server.c -lpthread -O2
  artifacts:
    paths:
      - seam-server
    expire_in: 1 week
```

### On Each Push

```bash
# Compile binary
gcc -o seam-server seam-server.c -lpthread -O2

# Deploy (example)
scp seam-server deploy@server:/opt/seam/

# Restart service
ssh deploy@server "systemctl restart seam-server"
```

## Performance

- **Memory**: ~2 MB base + 5 KB per task
- **Startup**: <10 ms
- **Concurrency**: ~100 simultaneous requests (limited by open file descriptors)
- **Response time**: <1 ms for /health, ~2 ms for /compounds

## Troubleshooting

### Build fails with "gcc: command not found"

Install a C compiler:
- **Ubuntu**: `sudo apt-get install build-essential`
- **macOS**: `xcode-select --install`
- **Windows**: Download [MinGW](https://www.mingw-w64.org/) or use [Windows Subsystem for Linux](https://docs.microsoft.com/windows/wsl)

### "Address already in use"

Port 5000 is taken. Kill the existing process:
```bash
# Linux/macOS
lsof -i :5000 | grep LISTEN | awk '{print $2}' | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

Or modify `#define PORT 5000` in `seam-server.c` and rebuild.

### CORS errors in browser

The server returns CORS headers automatically. If you still get errors:
1. Verify the frontend is on `http://localhost:*` (not `file://`)
2. Check browser console for the actual error
3. Try accessing `/health` directly: `http://localhost:5000/health`

## Security Notes

- Server binds to `127.0.0.1` (localhost only) by default
- No authentication required (fine for localhost)
- To expose on network, modify source: `htonl(INADDR_ANY)` instead of `htonl(INADDR_LOOPBACK)`

## License & Attribution

Part of the SEAM Structural Perturbation Analysis Engine.

Lock: `62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4`

---

**Next Steps:**
1. `./BUILD.sh` (or `BUILD.bat` on Windows)
2. `./seam-server`
3. Open `seam-ui-improved.html` in your browser
4. Select compounds and analyze!
