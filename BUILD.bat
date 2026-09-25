@echo off
REM SEAM C Server Build Script for Windows
REM Compiles minimal C HTTP server with no external dependencies

echo ================================================
echo Building SEAM C Server (Windows)
echo ================================================
echo.

REM Get version argument (default: enhanced)
set VERSION=%1
if "%VERSION%"=="" set VERSION=enhanced

if "%VERSION%"=="minimal" (
    set SOURCE=seam-server.c
    set OUTPUT=seam-server-minimal.exe
    echo Building MINIMAL version (hardcoded 5 compounds)...
) else if "%VERSION%"=="enhanced" (
    set SOURCE=seam-server-enhanced.c
    set OUTPUT=seam-server.exe
    echo Building ENHANCED version (loads 306 compounds from JSON)...
) else (
    echo Usage: BUILD.bat [minimal^|enhanced]
    echo   minimal  - Hardcoded 5 demo compounds, no file I/O
    echo   enhanced - Loads SEAM_common_drugs_supplements_choice_registry_v1.json
    pause
    exit /b 1
)

echo.

REM Check if gcc is available
where gcc >nul 2>nul
if errorlevel 1 (
    echo ERROR: gcc not found. Please install MinGW or use Windows Subsystem for Linux.
    echo.
    echo Download MinGW: https://www.mingw-w64.org/
    echo Or use Windows 11 WSL2: wsl --install
    pause
    exit /b 1
)

gcc -o %OUTPUT% %SOURCE% -lpthread -Wall -Wextra -O2

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo OK: Build successful!
    echo Binary: %OUTPUT%
    echo ================================================
    echo.
    echo To run:
    echo   %OUTPUT%
    echo.
    echo Test:
    echo   curl http://localhost:5000/health
    echo.
) else (
    echo ERROR: Build failed
    pause
    exit /b 1
)
