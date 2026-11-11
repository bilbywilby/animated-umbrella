#!/bin/bash
set -e

# Standardized target list to prevent inconsistency
TARGET_FILES=("tests/fixtures/baseline_2027.html" "cms_crosswalk.html")
REDACTED_VAL="pk.REDACTED_TOKEN"

echo "[*] Phase 1: Auditing for residual token fragments..."
# Use || true to prevent set -e from aborting on no-match (exit 1)
grep -R --exclude-dir=.git --line-number -E "pk\.[A-Za-z0-9_.-]+" "${TARGET_FILES[@]}" || echo "No raw tokens found."

echo "[*] Phase 2: Executing programmatic redaction via Python 3..."
python3 - <<'PY'
import re
import pathlib

targets = ["tests/fixtures/baseline_2027.html", "cms_crosswalk.html"]
# Regex: Matches "mapboxToken":"pk.<anything not a quote>"
# Replacement: Ensures the value is exactly "pk.REDACTED_TOKEN"
pattern = r'("mapboxToken":"pk\.[^"]+")'
replacement = '"mapboxToken":"pk.REDACTED_TOKEN"'

for p in targets:
    f = pathlib.Path(p)
    if not f.exists():
        print(f"Warning: {p} not found, skipping.")
        continue
    
    content = f.read_text(encoding='utf-8')
    # Using a lambda or direct replacement to ensure the full matched group is swapped
    new_content = re.sub(r'"mapboxToken":"pk\.[^"]+"', replacement, content)
    
    if content != new_content:
        f.write_text(new_content, encoding='utf-8')
        print(f"Processed and sanitized: {p}")
    else:
        print(f"No changes needed for: {p}")
PY

echo "[*] Phase 3: Final Compliance Verification..."
# 1. Confirm the redacted value is present
grep -R --exclude-dir=.git --line-number "mapboxToken\":\"$REDACTED_VAL" "${TARGET_FILES[@]}" || echo "Warning: Redacted value not found."

# 2. Ensure no suffixes remain (Must be empty)
SUFFIX_CHECK=$(grep -R --exclude-dir=.git --line-number -E "mapboxToken\":\"$REDACTED_VAL\." "${TARGET_FILES[@]}" || true)

if [ -z "$SUFFIX_CHECK" ]; then
    echo "[+] Verification Successful: Absolute redaction confirmed. No trailing suffixes."
else
    echo "[!] Verification Failed: Residual data detected."
    echo "$SUFFIX_CHECK"
    exit 1
fi
