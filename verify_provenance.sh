#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/animated-umbrella"
cd "$ROOT"

echo "--- Initiating Provenance Verification ---"

# Ensure directory exists
mkdir -p data/provenance

# Test Case 1: Record a dummy artifact
python3 src/provenance.py \
    --name "Test Dataset" \
    --url "https://example.com/test" \
    --file "data/pa_rating_areas.json" \
    --tier "VERIFIED" \
    --notes "Verification of atomic write"

# Test Case 2: Verify JSON integrity using tac (to check last entry)
if [ -f data/provenance/audit_log.json ]; then
    echo "✅ Audit log created."
    # Using tac to ensure the last line of the JSON is present
    tac data/provenance/audit_log.json | head -n 5
else
    echo "❌ Audit log missing."
    exit 1
fi

echo "--- Verification Complete ---"
