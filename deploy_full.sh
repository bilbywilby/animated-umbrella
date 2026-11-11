#!/usr/bin/env bash
# deploy_full.sh - Complete deployment with all fixes
set -euo pipefail

ROOT="$HOME/animated-umbrella"
cd "$ROOT"

red() { printf '\033[31m%s\033[0m\n' "$@"; }
green() { printf '\033[32m%s\033[0m\n' "$@"; }
yellow() { printf '\033[33m%s\033[0m\n' "$@"; }

step() { echo; green "=== $* ==="; }

# 1. Verify environment
step "Verify environment"
python3 --version
pip list | grep -E "pydantic|beautifulsoup4" || yellow "Some packages missing - installing..."
pip install pydantic beautifulsoup4 lxml -q

# 2. Parse CMS crosswalk (if not already done)
step "Parse CMS crosswalk"
if [ -f cms_crosswalk.html ]; then
    python3 src/parse_cms_crosswalk.py --input cms_crosswalk.html --output data/cms_county_to_area.json
else
    red "cms_crosswalk.html not found! Run: curl -sL https://www.cms.gov/.../pa-gra -o cms_crosswalk.html"
    exit 1
fi

# 3. Run full pipeline
step "Run full pipeline"
python3 src/tasks.py run

# 4. Deploy wiki
step "Deploy wiki"
WIKI_DIR="$ROOT/animated-umbrella.wiki"
if [ -d "$WIKI_DIR/.git" ]; then
    cd "$WIKI_DIR"
    git pull origin master
    cd "$ROOT"
else
    rm -rf "$WIKI_DIR"
    git clone https://github.com/bilbywilby/animated-umbrella.wiki.git "$WIKI_DIR"
fi

cp wiki_pages/*.md "$WIKI_DIR/"
cd "$WIKI_DIR"
git add .
git commit -m "Deploy: PHIAP Wiki with CMS-verified rating areas (Oct 10, 2026)" --allow-empty
git push origin master
cd "$ROOT"

# 5. Final verification
step "Final verification"
jq . HANDOVER.json > /dev/null 2>&1 && green "✅ HANDOVER.json valid" || red "❌ HANDOVER.json invalid"
ls data/cms_county_to_area.json >/dev/null 2>&1 && green "✅ CMS mapping exists" || red "❌ CMS mapping missing"
cd "$WIKI_DIR" && ls *.md | wc -l | grep -q 8 && green "✅ 8 wiki pages deployed" || red "❌ Wiki pages incomplete"
cd "$ROOT"

green "=========================================="
green "✅ DEPLOYMENT COMPLETE"
green "=========================================="
