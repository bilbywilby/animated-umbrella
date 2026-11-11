#!/usr/bin/env python3
"""Block failed citations before publication."""
import re, sys
from pathlib import Path

FAILED_PATTERNS = [r"SB\s*1071", r"Act\s*252-2023", r"28-725", r"29-8719", 
                   r"Bulletin\s*#?23-04", r"tidycov", r"House\s*Bill\s*1602"]

def scan(filepath):
    content = Path(filepath).read_text(errors='ignore')
    violations = [(p, len(re.findall(p, content, re.IGNORECASE))) 
                  for p in FAILED_PATTERNS if re.search(p, content, re.IGNORECASE)]
    if violations:
        print(f"❌ Triage FAILED: {filepath}")
        for p, n in violations:
            print(f"   Quarantined: '{p}' ({n}x)")
        return False
    print(f"✅ Triage PASSED: {filepath}")
    return True

if __name__ == "__main__":
    sys.exit(0 if scan(sys.argv[1]) else 1) if len(sys.argv) > 1 else print("Usage: python citation_triage.py <file>")
