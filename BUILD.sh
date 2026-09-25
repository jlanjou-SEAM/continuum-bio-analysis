#!/bin/bash
# SEAM C Server Build Script
# Compiles minimal C HTTP server with no external dependencies

echo "================================================"
echo "Building SEAM C Server"
echo "================================================"
echo ""

# Get version argument (default: enhanced which loads JSON)
VERSION=${1:-enhanced}

if [ "$VERSION" = "minimal" ]; then
    SOURCE="seam-server.c"
    OUTPUT="seam-server-minimal"
    echo "Building MINIMAL version (hardcoded 5 compounds)..."
elif [ "$VERSION" = "enhanced" ]; then
    SOURCE="seam-server-enhanced.c"
    OUTPUT="seam-server"
    echo "Building ENHANCED version (loads 306 compounds from JSON)..."
else
    echo "Usage: ./BUILD.sh [minimal|enhanced]"
    echo "  minimal  - Hardcoded 5 demo compounds, no file I/O"
    echo "  enhanced - Loads SEAM_common_drugs_supplements_choice_registry_v1.json"
    exit 1
fi

echo ""

# Detect platform
PLATFORM=$(uname -s)

if [ "$PLATFORM" = "Darwin" ]; then
    echo "macOS detected"
    gcc -o "$OUTPUT" "$SOURCE" -lpthread -Wall -Wextra -O2
elif [ "$PLATFORM" = "Linux" ]; then
    echo "Linux detected"
    gcc -o "$OUTPUT" "$SOURCE" -lpthread -Wall -Wextra -O2
else
    echo "Windows detected (MSYS2/Git Bash)"
    gcc -o "$OUTPUT.exe" "$SOURCE" -lpthread -Wall -Wextra -O2
    OUTPUT="$OUTPUT.exe"
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✓ Build successful!"
    echo "✓ Binary: $OUTPUT"
    echo "================================================"
    echo ""
    echo "To run:"
    echo "  ./$OUTPUT"
    echo ""
    echo "Test:"
    echo "  curl http://localhost:5000/health"
    echo ""
else
    echo "✗ Build failed"
    exit 1
fi
