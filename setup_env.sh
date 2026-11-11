#!/bin/bash
set -e
mkdir -p venv
python3 -m venv venv
source venv/bin/activate
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
else
    pip install pytest
fi
echo "Environment deployed. Use 'source venv/bin/activate' to begin."
