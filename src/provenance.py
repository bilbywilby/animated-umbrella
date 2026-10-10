#!/usr/bin/env python3
"""SHA-256 provenance tracking for audit artifacts."""
import hashlib, json, requests
from pathlib import Path
from datetime import datetime, timezone

class ProvenanceTracker:
    def __init__(self, output_dir="./data/provenance"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / f"provenance_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        self.entries = []
    
    def compute_hash(self, filepath):
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def record(self, name, url, filepath, tier, notes=""):
        entry = {
            "source_name": name, "url": url,
            "filepath": str(filepath.absolute()),
            "sha256_hash": self.compute_hash(filepath) if filepath.exists() else None,
            "tier": tier.upper(), "notes": notes,
            "timestamp_utc": datetime.now(timezone.utc).isoformat()
        }
        self.entries.append(entry)
        with open(self.log_file, 'w') as f:
            json.dump({"entries": self.entries}, f, indent=2)
        return entry
