#!/bin/bash
# Carter's Atomic Deployer
set -e

REPO_URL="git@github.com:bilbywilby/crostini-recovery.git"
TARGET_DIR="$HOME/github_deploy"

cd "$TARGET_DIR"

# Initialize repo if needed
if [ ! -d ".git" ]; then
    git init
    git remote add origin "$REPO_URL"
fi

# Pre-push validation using python3
python3 -c "
import os
files = ['env_restorer.py', 'diagnostic_gather.sh']
for f in files:
    if not os.path.exists(f):
        print(f'CRITICAL: {f} missing. Aborting.')
        exit(1)
print('Validation successful: All scripts present.')
"

# Stage and commit
git add .
git commit -m "Deployment of recovery scripts: $(date +%Y%m%d_%H%M)"

# Push to main
git push -u origin main
