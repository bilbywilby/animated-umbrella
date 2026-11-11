#!/bin/bash
# Carter's OPSEC Git Initializer
set -e

# Create directory structure
mkdir -p ~/github_deploy/scripts
cd ~/github_deploy

# Install dependencies
pkg install git openssh -y

# Configure Git identity
git config --global user.name "bilbywilby"
git config --global user.email "bilbywilby@opsec.local"
git config --global init.defaultBranch main

# Generate Ed25519 SSH key for maximum security
if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -C "bilbywilby@pixel-termux" -N ""
fi

# Output public key for manual entry into GitHub Settings -> SSH and GPG keys
echo "----------------------------------------------------------------"
echo "COPY THE FOLLOWING PUBLIC KEY TO GITHUB:"
cat ~/.ssh/id_ed25519.pub
echo "----------------------------------------------------------------"
