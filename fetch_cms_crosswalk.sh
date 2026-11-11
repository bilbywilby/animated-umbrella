#!/bin/bash
# OPSEC: Secure fetch of official CMS crosswalk for PA Rating Area verification
set -e

TARGET_URL="https://www.cms.gov/cciio/programs-and-initiatives/health-insurance-market-reforms/pa-gra"
OUTPUT_FILE="cms_crosswalk.html"
LOG_FILE="cms_fetch.log"

echo "[$(date +'%Y-%m-%dT%H:%M:%S')] Initiating fetch from $TARGET_URL" | tee -a "$LOG_FILE"

if curl -sL "$TARGET_URL" -o "$OUTPUT_FILE"; then
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] SUCCESS: CMS crosswalk saved to $OUTPUT_FILE" | tee -a "$LOG_FILE"
    # Verify file is not empty or a 404 page
    if grep -q "Rating Area" "$OUTPUT_FILE"; then
        echo "Content verification: PASSED"
    else
        echo "Content verification: FAILED (Expected keywords not found)"
        exit 1
    fi
else
    echo "[$(date +'%Y-%m-%dT%H:%M:%S')] ERROR: Network fetch failed" | tee -a "$LOG_FILE"
    exit 1
fi
