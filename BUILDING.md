# Building the C Backend

Complete instructions for building the SEAM Analyzer C backend from source.

## Requirements

- **C Compiler**: gcc, clang, or MSVC
- **pthreads**: Usually included with compiler
- **Make** (optional, for Makefile)

## Quick Start

### Linux / macOS
```bash
chmod +x BUILD.sh
./BUILD.sh enhanced
./seam-server
```

### Windows (MSYS2/Git Bash)
```bash
chmod +x BUILD.sh
./BUILD.sh enhanced
./seam-server.exe
```

### Windows (Command Prompt)
```cmd
gcc seam-server-enhanced.c -o seam-server.exe -lpthread -O2
seam-server.exe
```

## Build Methods

### Method 1: BUILD.sh Script (Recommended)

```bash
./BUILD.sh enhanced    # Production version (306 compounds from JSON)
./BUILD.sh minimal     # Demo version (5 hardcoded compounds)
```

**Output:**
- Linux/macOS: `./seam-server`
- Windows: `./seam-server.exe`

### Method 2: Direct GCC Compilation

**Enhanced (Production):**
```bash
gcc seam-server-enhanced.c -o seam-server -lpthread -Wall -Wextra -O2
```

**Minimal (Demo):**
```bash
gcc seam-server.c -o seam-server -lpthread -Wall -Wextra -O2
```

**Windows (MinGW):**
```bash
gcc seam-server-enhanced.c -o seam-server.exe -lpthread -Wall -Wextra -O2
seam-server.exe
```

### Method 3: Make (if Makefile available)

```bash
make
make run
```

## Verify Build

Test that the server built correctly:

```bash
./seam-server &
sleep 1
curl http://localhost:5000/health
```

Expected response:
```json
{
  "status": "ok",
  "lock_hash": "62c6aa75effef85b9039251fd7fd2dae7e11b676e861f71ac7892f33a1bd85e4",
  "compounds": 306
}
```

## Platform-Specific Notes

### Linux
```bash
# Install build tools if needed
sudo apt-get install build-essential

# Build
gcc seam-server-enhanced.c -o seam-server -lpthread -O2

# Run
./seam-server
```

### macOS
```bash
# Install Xcode tools if needed
xcode-select --install

# Build
gcc seam-server-enhanced.c -o seam-server -lpthread -O2

# Run
./seam-server
```

### Windows (MinGW)
```bash
# Install MinGW from: https://www.mingw-w64.org/

# Build
gcc seam-server-enhanced.c -o seam-server.exe -lpthread -O2

# Run
seam-server.exe
```

### Windows (WSL2)
```bash
# Inside WSL2 (Ubuntu)
gcc seam-server-enhanced.c -o seam-server -lpthread -O2
./seam-server
```

### Windows (MSVC)
```bash
# Visual Studio Developer Command Prompt
cl seam-server-enhanced.c /link pthreads.lib
seam-server.exe
```

## File Structure

```
continuum-bio-analysis/
├── seam-server-enhanced.c      # Production source (loads 306 compounds)
├── seam-server.c                # Minimal demo source (5 compounds)
├── seam-server-windows.c        # Windows-specific variant
├── BUILD.sh                      # Build script
├── seam-ui-improved.html         # Frontend
├── SEAM_common_drugs_supplements_choice_registry_v1.json
├── conditions_database.json
└── structure_database.json
```

## Compilation Flags Explained

- `-o seam-server` — Output binary name
- `-lpthread` — Link pthreads library
- `-Wall` — Show all warnings
- `-Wextra` — Show extra warnings
- `-O2` — Optimization level 2

## Troubleshooting

### "gcc: command not found"
Install a C compiler for your platform (see Platform-Specific Notes above)

### "undefined reference to pthread_create"
Ensure you included `-lpthread` flag

### "Port 5000 already in use"
Change port in source code or kill existing process:
```bash
# Linux/macOS
lsof -i :5000
kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### Server starts but frontend can't connect
- Verify server is running: `curl http://localhost:5000/health`
- Check firewall settings
- Ensure frontend is accessing `http://localhost:5000` (not https)

## Running the Server

Once built:

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

Then open the frontend:
https://jlanjou-SEAM.github.io/continuum-bio-analysis/seam-ui-improved.html

## Performance

- **Binary size**: ~200KB
- **Startup time**: <10ms
- **Memory usage**: ~5MB (with 306 compounds loaded)
- **Analysis time**: 1-3 seconds per request
- **Concurrent connections**: Limited by thread pool

## License

Proprietary — All Rights Reserved
