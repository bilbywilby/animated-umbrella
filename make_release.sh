#!/bin/bash
set -e

# Configuration
ROOT_DIR="$HOME/animated-umbrella"
SRC_DIR="$ROOT_DIR/src"
DATA_DIR="$ROOT_DIR/data"
OUT_DIR="$ROOT_DIR/final_package"

cd "$ROOT_DIR"

echo "--- [1/6] Generating Base Datasets ---"
python3 "$SRC_DIR/generate_full_dataset.py"
python3 "$SRC_DIR/generate_pid_data.py"

echo "--- [2/6] Rendering Analysis Artifacts ---"
python3 "$SRC_DIR/build_one_pagers.py"
python3 "$SRC_DIR/generate_briefing_html.py"

echo "--- [3/6] Exporting PDF via Playwright ---"
node generate_pdf_cdp.js

echo "--- [4/6] Establishing Provenance ---"
mkdir -p "$DATA_DIR/provenance"
python3 "$SRC_DIR/provenance.py" \
  --url "https://www.pid.state.pa.us" \
  --file "$DATA_DIR/pa_ra_dataset.json" \
  --tier "VERIFIED" \
  --name "PY2027 Audit Dataset"

echo "--- [5/6] Citation Triage & Validation ---"
python3 "$SRC_DIR/citation_triage.py" pa_aca_briefing_py2027_final.html

echo "--- [6/6] Packaging Release ---"
mkdir -p "$OUT_DIR/data" "$OUT_DIR/docs"
cp -r "$DATA_DIR"/* "$OUT_DIR/data/"
cp *.html *.md "$OUT_DIR/docs/"
tar -czf pa_aca_briefing_py2027_release.tar.gz -C "$ROOT_DIR" final_package

echo "✅ Audit Pipeline Complete. Artifacts ready in $OUT_DIR"
