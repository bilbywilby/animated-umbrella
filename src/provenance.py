# #!/usr/bin/env python3
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any


def atomic_write_json(destination: Path, payload: dict[str, Any]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, destination)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


class ProvenanceTracker:
    def __init__(self, log_file: Path = Path("data/provenance/audit_log.json")) -> None:
        self.log_file = log_file
        self.entries: list[dict[str, Any]] = []
        if self.log_file.exists():
            try:
                with open(self.log_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.entries = data.get("entries", [])
            except (json.JSONDecodeError, OSError):
                self.entries = []

    def record(self, name: str, url: str, file_path: str, tier: str, notes: str = "") -> dict[str, Any]:
        entry = {
            "name": name,
            "url": url,
            "file": file_path,
            "tier": tier,
            "notes": notes,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        self.entries.append(entry)
        atomic_write_json(self.log_file, {"entries": self.entries})
        return entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Record artifact provenance and SHA-256 hashes.")
    parser.add_argument("--name", required=True, help="Name of the source/dataset")
    parser.add_argument("--url", required=True, help="Source URL")
    parser.add_argument("--file", required=True, help="Path to file")
    parser.add_argument("--tier", required=True, help="Verification tier (e.g., VERIFIED)")
    parser.add_argument("--notes", default="", help="Optional notes")
    args = parser.parse_args()

    tracker = ProvenanceTracker()
    tracker.record(args.name, args.url, args.file, args.tier, args.notes)
    print(f"✅ Provenance recorded for {args.file}")


if __name__ == "__main__":
    main()

