#!/usr/bin/env bash
set -euo pipefail

ROOT="$HOME/animated-umbrella"
WIKI_DIR="$ROOT/animated-umbrella.wiki"
cd "$ROOT"

# Clone wiki if not exists
if [ ! -d "$WIKI_DIR" ]; then
    git clone https://github.com/bilbywilby/animated-umbrella.wiki.git "$WIKI_DIR"
fi

# Copy the 8 audited pages (assuming they are in a 'wiki_pages' directory or similar)
# Adjust source path as necessary based on where the .md files currently reside
cp ./wiki_pages/*.md "$WIKI_DIR/" 2>/dev/null || echo "Warning: Source .md files not found in ./wiki_pages/"

cd "$WIKI_DIR"
git add .
git commit -m "Refactor: Integrate PA Health Insurance Audit files, verification pipeline, and schemas (Oct 10, 2026)"
git push origin master

echo "✅ Wiki Deployment Successful."
