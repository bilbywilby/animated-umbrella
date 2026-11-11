#!/usr/bin/env bash
set -euo pipefail

# Use w3m to dump the CMS crosswalk for verification
# We are looking for "Rating Area 1" and "Rating Area 7" proximity to specific counties
w3m -dump https://www.cms.gov/cciio/programs-and-initiatives/health-insurance-market-reforms/pa-gra > cms_dump.txt

echo "--- CMS CROSSWALK VERIFICATION ---"
echo "Area 1 Check (Northwest):"
grep -A 5 "Rating Area 1" cms_dump.txt | grep -E "Erie|Warren|McKean" || echo "❌ Area 1 mismatch"

echo "Area 7 Check (Lehigh Valley):"
grep -A 5 "Rating Area 7" cms_dump.txt | grep -E "Lehigh|Northampton" || echo "❌ Area 7 mismatch"
