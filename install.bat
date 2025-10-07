@echo off
REM Market Analyzer v5.0 - Windows Installation Script

echo ==========================================
echo Market Analyzer v5.0 - Installation
echo ==========================================
echo.

REM Check Python installation
echo Checking Python installation...
py --version >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [OK] Python found: %PYTHON_VERSION%
) else (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo.

REM Check pip installation
echo Checking pip installation...
py -m pip --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] pip found
) else (
    echo [ERROR] pip not found!
    echo Installing pip...
    python -m ensurepip --upgrade
)

echo.

REM Install required packages
echo Installing required packages...
echo.

echo 1. Installing requests...
py -m pip install requests

echo.
echo 2. Installing beautifulsoup4...
py -mpip install beautifulsoup4

echo.
echo 3. Installing lxml...
py -mpip install lxml

echo.
echo 4. Installing brotli (for NSE API decompression)...
py -mpip install brotli

echo.
echo ==========================================
echo [OK] Installation Complete!
echo ==========================================
echo.
echo Run the analyzer:
echo   python market_analyzer_v5_integrated.py
echo.
echo Read the production guide:
echo   type V5_PRODUCTION_GUIDE.md
echo.
echo Quick start guide:
echo   type QUICKSTART.md
echo.
echo Output files will be saved as:
echo   signals_HIGH_YYYY-MM-DD.txt
echo   signals_MEDIUM_YYYY-MM-DD.txt
echo   signals_LOW_YYYY-MM-DD.txt
echo.
echo ==========================================
echo.
pause
