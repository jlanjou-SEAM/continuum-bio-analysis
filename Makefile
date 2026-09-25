# SEAM Analyzer C Backend Makefile
# Minimal C HTTP server for structural perturbation analysis

CC = gcc
CFLAGS = -Wall -Wextra -O2 -lpthread
SOURCES_ENHANCED = seam-server-enhanced.c
SOURCES_MINIMAL = seam-server.c
TARGET_ENHANCED = seam-server
TARGET_MINIMAL = seam-server-minimal

.PHONY: all enhanced minimal clean run help

# Default target
all: enhanced

# Production version (306 compounds from JSON)
enhanced:
	@echo "Building SEAM Server (enhanced - 306 compounds)..."
	$(CC) $(CFLAGS) $(SOURCES_ENHANCED) -o $(TARGET_ENHANCED)
	@echo "✓ Build successful: ./$(TARGET_ENHANCED)"

# Minimal demo version (5 hardcoded compounds)
minimal:
	@echo "Building SEAM Server (minimal - demo)..."
	$(CC) $(CFLAGS) $(SOURCES_MINIMAL) -o $(TARGET_MINIMAL)
	@echo "✓ Build successful: ./$(TARGET_MINIMAL)"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -f $(TARGET_ENHANCED) $(TARGET_MINIMAL) *.o *.exe
	@echo "✓ Clean complete"

# Run the enhanced server
run: enhanced
	@echo "Starting SEAM Server on http://localhost:5000"
	./$(TARGET_ENHANCED)

# Show help
help:
	@echo "SEAM Analyzer C Backend - Makefile"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  all       - Build production version (default)"
	@echo "  enhanced  - Build production server (306 compounds)"
	@echo "  minimal   - Build minimal demo server (5 compounds)"
	@echo "  run       - Build and run production server"
	@echo "  clean     - Remove build artifacts"
	@echo "  help      - Show this message"
	@echo ""
	@echo "Examples:"
	@echo "  make              # Build enhanced version"
	@echo "  make run          # Build and run"
	@echo "  make minimal      # Build minimal demo"
	@echo "  make clean        # Clean artifacts"
