#!/bin/bash
# Market Analyzer v5.0 - Installation Script

echo "=========================================="
echo "Market Analyzer v5.0 - Installation"
echo "=========================================="
echo ""

# Check Python installation
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Python found: $PYTHON_VERSION"
else
    echo "✗ Python 3 not found!"
    echo "Please install Python 3.8+ from https://www.python.org/downloads/"
    exit 1
fi

echo ""

# Check pip installation
echo "Checking pip installation..."
if command -v pip3 &> /dev/null; then
    echo "✓ pip3 found"
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    echo "✓ pip found"
    PIP_CMD="pip"
else
    echo "✗ pip not found!"
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
    PIP_CMD="pip3"
fi

echo ""

# Install required packages
echo "Installing required packages..."
echo ""

echo "1. Installing requests..."
$PIP_CMD install requests --break-system-packages 2>/dev/null || $PIP_CMD install requests

echo "2. Installing beautifulsoup4..."
$PIP_CMD install beautifulsoup4 --break-system-packages 2>/dev/null || $PIP_CMD install beautifulsoup4

echo "3. Installing lxml..."
$PIP_CMD install lxml --break-system-packages 2>/dev/null || $PIP_CMD install lxml

echo "4. Installing brotli (for NSE API decompression)..."
$PIP_CMD install brotli --break-system-packages 2>/dev/null || $PIP_CMD install brotli

echo ""
echo "=========================================="
echo "✓ Installation Complete!"
echo "=========================================="
echo ""
echo "🚀 Run the analyzer:"
echo "  python3 market_analyzer_v5_integrated.py"
echo ""
echo "📚 Read the production guide:"
echo "  cat V5_PRODUCTION_GUIDE.md"
echo ""
echo "⚡ Quick start guide:"
echo "  cat QUICKSTART.md"
echo ""
echo "📊 Output files will be saved as:"
echo "  signals_HIGH_YYYY-MM-DD.txt"
echo "  signals_MEDIUM_YYYY-MM-DD.txt"
echo "  signals_LOW_YYYY-MM-DD.txt"
echo ""
echo "=========================================="
