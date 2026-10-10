#!/usr/bin/env bash
set -eu

ROOT="$HOME/animated-umbrella"
cd "$ROOT"

printf '%s\n' '=== System ==='
uname -a
printf 'Python: '; python3 --version
printf 'Node: '; node --version 2>/dev/null || true
printf 'npm: '; npm --version 2>/dev/null || true
printf '\n%s\n' '=== Git status ==='
git status --short --branch
printf '\n%s\n' '=== Recent commits ==='
git log -5 --oneline 2>/dev/null || true
printf '\n%s\n' '=== Diff summary ==='
git diff --stat
git diff --cached --stat
printf '\n%s\n' '=== Project files (excluding generated/dependency directories) ==='
find . -maxdepth 3 \
  \( -name .git -o -name node_modules -o -name __pycache__ -o -name final_package \) -prune \
  -o -type f -print | sort
printf '\n%s\n' '=== Pipeline syntax checks ==='
bash -n ./make_release.sh 2>&1 || true
python3 -m compileall -q src 2>&1 || true
printf '\n%s\n' '=== Relevant file sizes ==='
wc -l .gitignore make_release.sh src/*.py 2>/dev/null || true
