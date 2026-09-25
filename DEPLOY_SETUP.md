# Deployment & Setup Guide

Complete setup instructions for running the SEAM analyzer in production.

## System Requirements

### To Build
- **C compiler**: GCC, Clang, or MSVC (all work)
- **No other dependencies**
- Supports: Linux, macOS, Windows (MinGW/WSL)

### To Run
- Port 5000 available (or edit source to change)
- ~2 MB RAM per instance

## Installation

### 1. Prepare Files

Ensure these files are present:

```
/path/to/seam/
├── seam-server-enhanced.c        (loads 306 compounds)
├── seam-server.c                 (optional: minimal hardcoded)
├── seam-ui-improved.html         (frontend)
├── BUILD.sh                       (Unix build script)
├── BUILD.bat                      (Windows build script)
└── SEAM_common_drugs_supplements_choice_registry_v1.json
```

### 2. Build the Server

#### macOS / Linux
```bash
cd /path/to/seam
chmod +x BUILD.sh
./BUILD.sh enhanced
```

#### Windows (MinGW)
```cmd
cd C:\path\to\seam
BUILD.bat enhanced
```

#### Windows (WSL)
```bash
# Inside WSL
cd /mnt/d/seam  # or wherever your files are
./BUILD.sh enhanced
```

#### Manual Build
```bash
gcc -o seam-server seam-server-enhanced.c -lpthread -Wall -Wextra -O2
```

### 3. Verify Build

```bash
ls -lh seam-server        # Should show ~200-300 KB
file seam-server          # Should say "ELF 64-bit" (Linux) or "Mach-O" (macOS)
```

### 4. Test Locally

**Terminal 1: Start server**
```bash
./seam-server
```

Expected output:
```
============================================================
  SEAM Compound Analyzer Backend
  Minimal C Server (No Dependencies)
============================================================
✓ Lock: 62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4
✓ Server starting on http://localhost:5000
✓ Database: 306 compounds loaded
============================================================
```

**Terminal 2: Test endpoints**
```bash
# Check health
curl http://localhost:5000/health

# Get compound list
curl http://localhost:5000/compounds | jq '.count'

# Submit analysis
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"compounds": ["Famotidine"]}'

# Poll results
curl http://localhost:5000/results/task_1
```

### 5. Run Frontend

Open **seam-ui-improved.html** in a web browser:
- `file:///path/to/seam/seam-ui-improved.html`

Or use a local web server:
```bash
# Python 3
python3 -m http.server 8080

# Node
npx http-server

# Live Server (VS Code)
# Right-click HTML → "Open with Live Server"
```

Then visit: `http://localhost:8080/seam-ui-improved.html`

## Production Deployment

### Docker

**Dockerfile**
```dockerfile
FROM gcc:12-alpine AS builder
WORKDIR /build
COPY seam-server-enhanced.c BUILD_LOCK_HASH.md ./
RUN gcc -o seam-server seam-server-enhanced.c -lpthread -O2

FROM alpine:latest
WORKDIR /app
COPY --from=builder /build/seam-server .
COPY SEAM_common_drugs_supplements_choice_registry_v1.json .
COPY seam-ui-improved.html .
EXPOSE 5000
CMD ["./seam-server"]
```

**Build & Run**
```bash
docker build -t seam-analyzer .
docker run -p 5000:5000 seam-analyzer
```

### Linux Systemd Service

**File: /etc/systemd/system/seam-analyzer.service**
```ini
[Unit]
Description=SEAM Compound Analyzer Backend
After=network.target

[Service]
Type=simple
User=seam
WorkingDirectory=/opt/seam
ExecStart=/opt/seam/seam-server
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Deploy**
```bash
# Copy binary and data
sudo cp seam-server /opt/seam/
sudo cp SEAM_common_drugs_supplements_choice_registry_v1.json /opt/seam/
sudo chown -R seam:seam /opt/seam

# Enable and start
sudo systemctl enable seam-analyzer
sudo systemctl start seam-analyzer

# Check status
sudo systemctl status seam-analyzer

# Logs
sudo journalctl -u seam-analyzer -f
```

### Kubernetes

**seam-deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: seam-analyzer
spec:
  replicas: 3
  selector:
    matchLabels:
      app: seam-analyzer
  template:
    metadata:
      labels:
        app: seam-analyzer
    spec:
      containers:
      - name: seam-server
        image: seam-analyzer:latest
        ports:
        - containerPort: 5000
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 3
          periodSeconds: 5
        resources:
          limits:
            memory: "64Mi"
            cpu: "100m"
          requests:
            memory: "32Mi"
            cpu: "50m"
---
apiVersion: v1
kind: Service
metadata:
  name: seam-analyzer
spec:
  selector:
    app: seam-analyzer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 5000
  type: LoadBalancer
```

**Deploy**
```bash
kubectl apply -f seam-deployment.yaml
kubectl get pods -l app=seam-analyzer
kubectl logs -l app=seam-analyzer
```

### CI/CD Integration

#### GitHub Actions
```yaml
name: Build & Deploy SEAM Server

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build C server
        run: |
          chmod +x BUILD.sh
          ./BUILD.sh enhanced
      
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: seam-server
          path: seam-server
      
      - name: Build Docker image
        run: |
          docker build -t seam-analyzer:${{ github.sha }} .
          docker tag seam-analyzer:${{ github.sha }} seam-analyzer:latest
      
      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push seam-analyzer:latest
```

#### GitLab CI
```yaml
stages:
  - build
  - deploy

build:
  stage: build
  image: gcc:latest
  script:
    - gcc -o seam-server seam-server-enhanced.c -lpthread -O2
  artifacts:
    paths:
      - seam-server
    expire_in: 1 week

deploy:
  stage: deploy
  image: docker:latest
  script:
    - docker build -t seam-analyzer .
    - docker tag seam-analyzer registry.example.com/seam-analyzer
    - docker push registry.example.com/seam-analyzer
  only:
    - main
```

## Configuration

### Change Port

Edit `seam-server-enhanced.c`:
```c
#define PORT 5000  // Change this
```

Then rebuild:
```bash
gcc -o seam-server seam-server-enhanced.c -lpthread -O2
```

### Custom Database Path

Edit `seam-server-enhanced.c`:
```c
#define DATABASE_PATH "SEAM_common_drugs_supplements_choice_registry_v1.json"  // Change this
```

### Bind to All Interfaces

Edit `seam-server-enhanced.c`, in `main()`:
```c
// Change this line:
addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);

// To this:
addr.sin_addr.s_addr = htonl(INADDR_ANY);
```

Then rebuild.

## Performance Tuning

### Increase Max Concurrent Tasks

Edit `seam-server-enhanced.c`:
```c
#define MAX_TASKS 1000  // Default: 100
```

### Increase Buffer Size

For very large compound lists:
```c
#define BUFFER_SIZE 262144  // Default: 131072
```

### Optimize Build

```bash
gcc -O3 -march=native -o seam-server seam-server-enhanced.c -lpthread
```

## Security Notes

### TLS/HTTPS

Add OpenSSL (requires dependency):
```bash
gcc -o seam-server seam-server-enhanced.c -lpthread -lssl -lcrypto -O2
```

Or use a reverse proxy:
```bash
# Nginx in front of seam-server:5000
http://localhost:5000 <-- internal
     ^
  [nginx on :443]
     ^
  user (HTTPS)
```

### Authentication

Currently: None (localhost only)

To add API key:
1. Modify `seam-server-enhanced.c` to check `Authorization` header
2. Verify against hardcoded key or env var
3. Return 401 if missing/invalid

### Firewall

Default: Binds to `127.0.0.1` (localhost only)

To expose on network: Modify `addr.sin_addr.s_addr` (see above)

Then restrict with firewall:
```bash
# Linux firewall
sudo ufw allow 5000/tcp from 192.168.1.0/24

# macOS firewall
# System Preferences → Security → Firewall Options
```

## Monitoring

### Health Check

```bash
curl -s http://localhost:5000/health | jq .
```

### Prometheus Metrics

Would require code changes. For now, use:
```bash
curl -s http://localhost:5000/health | jq '.compounds' > /tmp/seam_compounds.txt
```

### Logs

Server writes to stdout. Capture with:
```bash
# File
./seam-server > /var/log/seam-server.log 2>&1 &

# Syslog
./seam-server 2>&1 | logger -t seam-server &
```

## Maintenance

### Restart

```bash
# Find PID
lsof -i :5000
# or
ps aux | grep seam-server

# Kill & restart
kill -9 <PID>
./seam-server &
```

### Update Database

```bash
# Edit JSON file
nano SEAM_common_drugs_supplements_choice_registry_v1.json

# Restart server (no rebuild needed, loads at startup)
kill -9 $(lsof -t -i :5000)
./seam-server &
```

### Backup

```bash
# Backup binary + data
tar czf seam-analyzer-backup-$(date +%Y%m%d).tar.gz \
  seam-server \
  SEAM_common_drugs_supplements_choice_registry_v1.json
```

## Troubleshooting

### Port Already in Use
```bash
lsof -i :5000
netstat -tulnp | grep 5000  # Linux
netstat -ano | findstr :5000  # Windows
```

### Build Fails: gcc not found
- **macOS**: `xcode-select --install`
- **Ubuntu**: `sudo apt install build-essential`
- **Fedora**: `sudo dnf install gcc`
- **Windows**: Install [MinGW](https://www.mingw-w64.org/)

### Compounds Not Loading
```bash
# Check file exists
ls -la SEAM_common_drugs_supplements_choice_registry_v1.json

# Check permissions
chmod 644 SEAM_common_drugs_supplements_choice_registry_v1.json

# Verify JSON is valid
cat SEAM_common_drugs_supplements_choice_registry_v1.json | jq . > /dev/null
```

### CORS Errors in Frontend
- Ensure frontend is `http://`, not `file://`
- Check browser console for actual error
- Server returns CORS headers automatically

## Support

### Build Issues
1. Verify C compiler installed: `gcc --version`
2. Try different compiler: `clang`, `cc`
3. Check file permissions

### Runtime Issues
1. Check port not in use: `lsof -i :5000`
2. Verify database file readable: `cat SEAM_...json`
3. Check logs: stdout from `./seam-server`

---

**Ready?** Start with step 1 above, or skip to your deployment platform.
