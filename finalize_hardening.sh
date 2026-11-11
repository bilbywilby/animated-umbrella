#!/usr/bin/env bash
set -euo pipefail

# Define the function directly in the script to avoid quoting hell
safe_clone() {
    local repo_url="$1"
    local target_dir
    target_dir=$(basename "$repo_url" .git)

    if [ -d ".git" ]; then
        echo "ERROR: Refusing to clone inside an existing git repository root." >&2
        return 1
    fi

    if [ -d "$target_dir" ]; then
        echo "ERROR: Target directory '$target_dir' already exists." >&2
        return 1
    fi

    git clone "$repo_url"
}

readonly BASHRC="$HOME/.bashrc"

# Use declare -f to capture the function body as a literal string
if grep -q "safe_clone()" "$BASHRC" 2>/dev/null; then
    echo "[!] safe_clone already exists in $BASHRC. Skipping append."
else
    echo "Adding safe_clone guard to $BASHRC..."
    # Extract function definition and append it
    declare -f safe_clone >> "$BASHRC"
    echo 'alias gclone="safe_clone"' >> "$BASHRC"
    echo "[+] Guard deployed. Use 'gclone <url>' for safe operations."
fi

# Stream Pollution Mitigation
if ! grep -q "alias sink=" "$BASHRC" 2>/dev/null; then
    echo "alias sink='cat > /dev/null'" >> "$BASHRC"
    echo "[+] 'sink' alias added to neutralize pasted stdout."
fi

source "$BASHRC"
echo "[+] Shell environment successfully hardened and reloaded."
