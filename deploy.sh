#!/bin/bash
set -e

cd ~/animated-umbrella

echo "=== Phase 1: Validation ==="
python3 build_one_pagers.py --check

echo "=== Phase 2: Provenance ==="
python3 src/provenance.py \
  --url https://www.pid.state.pa.us \
  --file data/pa_ra_dataset.json \
  --tier VERIFIED \
  --name "PY2027 Audit Dataset"

echo "=== Phase 3: Triage ==="
python3 src/citation_triage.py pa_aca_briefing_py2027_final.html

echo "=== Phase 4: Final Commit ==="
git add data/* *.html
git commit -m "feat(audit): complete PY2027 dataset and deployment"
git push origin main

echo "=== Deployment Complete ==="
