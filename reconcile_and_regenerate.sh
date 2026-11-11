#!/usr/bin/env bash
set -euo pipefail

R="${1:-$HOME/animated-umbrella}"
cd "$R"

red() { printf '\033[31m%s\033[0m\n' "$@"; }
green() { printf '\033[32m%s\033[0m\n' "$@"; }
yellow() { printf '\033[33m%s\033[0m\n' "$@"; }

step() { echo; green "=== STEP: $* ==="; }

# Backup current state
step "Backup current datasets"
tar -czf "backup_$(date +%Y%m%d_%H%M%S).tar.gz" \
  data/pa_ra_dataset.json data/pa_rating_areas.json || true

# Fetch CMS crosswalk
step "Fetch CMS crosswalk"
curl -s 'https://www.cms.gov/cciio/programs-and-initiatives/health-insurance-market-reforms/pa-gra' \
  -o cms_crosswalk.html
if [ ! -s cms_crosswalk.html ]; then
  red "Failed to fetch CMS crosswalk"
  exit 1
fi
green "Downloaded: $(wc -c < cms_crosswalk.html) bytes"

# Parse crosswalk
step "Parse CMS crosswalk"
python3 src/parse_cms_crosswalk.py --input cms_crosswalk.html --output cms_county_to_area.json

# Validate changes
step "Validate mapping changes"
python3 src/validate_rating_areas.py || {
  yellow "Validation flagged changes. Review before continuing."
  read -p "Continue? (y/N) " -n 1 -r
  echo
  [[ $REPLY =~ ^[Yy]$ ]] || exit 0
}

# Regenerate dataset
step "Regenerate pa_ra_dataset.json"
python3 src/generate_full_dataset.py

# Regenerate HTML briefing
step "Regenerate HTML briefing"
python3 src/generate_briefing_html.py

# Record provenance
step "Record provenance"
python3 src/provenance.py \
  --name "PY2027 Dataset (CMS-Verified Mapping)" \
  --url "https://www.cms.gov/cciio/programs-and-initiatives/health-insurance-market-reforms/pa-gra" \
  --file data/pa_ra_dataset.json \
  --tier VERIFIED \
  --checksum

python3 src/provenance.py \
  --name "HTML Briefing (PY2027)" \
  --url "https://github.com/bilbywilby/animated-umbrella" \
  --file pa_aca_briefing_py2027_final.html \
  --tier VERIFIED

green "✅ Pipeline complete"
green "Backup: backup_*.tar.gz"
green "Next: Update Wiki and run citation_triage.py"
