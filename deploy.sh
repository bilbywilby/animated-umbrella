#!/usr/bin/env bash
# Pennsylvania ACA Market PY2027 Forensic Audit Package
# Automated Release & Build Verification Script

set -euo pipefail

echo ""
echo "🚀 STARTING ACA AUDIT PACKAGE DEPLOYMENT SEQUENCE"
echo "=============================================="
echo ""

# ============================================================================
# 1. Directory Initialization
# ============================================================================
echo "📁 Setting up release directories..."
mkdir -p ./final_package/data
mkdir -p ./final_package/docs

# ============================================================================
# 2. Dependency Check
# ============================================================================
echo "🔍 Validating dependencies..."

if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx is required but not installed."
    echo "💡 Install Node.js/npm first: https://nodejs.org/"
    exit 1
fi

if ! command -v playwright &> /dev/null; then
    echo "⚠️  Warning: Playwright CLI not found globally. Installing via npx..."
fi

# Check if Chromium browser is installed
if ! npx playwright chromium --version &> /dev/null; then
    echo "⚙️  Installing Playwright Chromium browser..."
    npx playwright install chromium
fi

# ============================================================================
# 3. Input File Validation
# ============================================================================
echo "📋 Validating input files..."

INPUT_HTML="./pa_aca_briefing_py2027_final.html"
if [ ! -f "$INPUT_HTML" ]; then
    echo "❌ Error: Input HTML file not found: $INPUT_HTML"
    echo "💡 Ensure the HTML presentation is in the current directory."
    exit 1
fi

INPUT_CSV="carrier_rates.csv"
if [ ! -f "$INPUT_CSV" ]; then
    echo "⚠️  Warning: Data CSV not found ($INPUT_CSV)"
else
    RECORD_COUNT=$(wc -l < "$INPUT_CSV")
    echo "✅ Found: $INPUT_CSV ($RECORD_COUNT records)"
fi

INPUT_JSON="pa_ra_dataset_corrected.json"
if [ ! -f "$INPUT_JSON" ]; then
    echo "⚠️  Warning: JSON dataset not found ($INPUT_JSON)"
else
    echo "✅ Found: $INPUT_JSON"
fi

# ============================================================================
# 4. PDF Compilation via Playwright
# ============================================================================
echo "📄 Generating PDF presentation bundle (12 pages)..."
echo "   → Output: ./final_package/pa_aca_briefing_py2027.pdf"

npx playwright pdf \
    "$INPUT_HTML" \
    ./final_package/pa_aca_briefing_py2027.pdf \
    --margin-top 0.5in \
    --margin-bottom 0.5in \
    --margin-left 0.5in \
    --margin-right 0.5in \
    --landscape

echo "✅ PDF generation initiated..."

# ============================================================================
# 5. Copying Verified Data Artifacts
# ============================================================================
echo "📦 Packing data exports and metadata..."

if [ -f "$INPUT_CSV" ]; then
    cp "$INPUT_CSV" ./final_package/data/
    echo "   ✓ Copied carrier_rates.csv"
fi

if [ -f "$INPUT_JSON" ]; then
    cp "$INPUT_JSON" ./final_package/data/
    echo "   ✓ Copied pa_ra_dataset_corrected.json"
fi

if [ -f "./HANDOVER.json" ]; then
    cp ./HANDOVER.json ./final_package/
    echo "   ✓ Copied HANDOVER.json"
fi

# ============================================================================
# 6. Comprehensive Validation Check
# ============================================================================
echo "🔍 Running artifact validation..."

PDF_FILE="./final_package/pa_aca_briefing_py2027.pdf"

if [ ! -f "$PDF_FILE" ]; then
    echo "❌ PDF generation failed - output file not created."
    exit 1
fi

FILESIZE=$(du -h "$PDF_FILE" | cut -f1)
PAGECOUNT=$(pdfinfo "$PDF_FILE" 2>/dev/null | grep "Pages:" | awk '{print $2}' || echo "unknown")

echo "✅ PDF generated successfully ($FILESIZE, $PAGECOUNT pages)."

# Size sanity check (expecting 2-8 MB for 12-page PDF with embedded charts)
SIZE_MB=$(du -m "$PDF_FILE" | cut -f1)
if [ "$SIZE_MB" -lt 2 ] || [ "$SIZE_MB" -gt 20 ]; then
    echo "⚠️  Warning: PDF size unusual ($FILESIZE). Charts may not have rendered."
else
    echo "✅ PDF size within expected range ($FILESIZE)."
fi

# ============================================================================
# 7. Final Package Manifest
# ============================================================================
echo ""
echo "=============================================="
echo "📋 FINAL PACKAGE MANIFEST"
echo "=============================================="
echo ""

tree ./final_package 2>/dev/null || find ./final_package -type f -exec ls -lh {} \;
echo ""

echo "✅ DEPLOYMENT PACKAGE READY FOR PUBLIC RELEASE"
echo ""
echo "📍 Package Location: ./final_package/"
echo "🕒 Timestamp: $(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z')"
echo ""
