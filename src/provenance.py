#!/usr/bin/env python3
"""Record artifact provenance and SHA-256 hashes."""

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
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
                data = json.loads(self.log_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise RuntimeError(f"Cannot read provenance log: {self.log_file}") from exc

            if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
                raise RuntimeError(f"Invalid provenance log structure: {self.log_file}")
            self.entries = data["entries"]

    @staticmethod
    def compute_hash(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def record(
        self, name: str, url: str, file_path: str, tier: str, notes: str = ""
    ) -> dict[str, Any]:
        path = Path(file_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Artifact does not exist or is not a file: {path}")

        entry = {
            "name": name,
            "url": url,
            "file": str(path.resolve()),
            "sha256_hash": self.compute_hash(path),
            "tier": tier.upper(),
            "notes": notes,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        }
        self.entries.append(entry)
        atomic_write_json(self.log_file, {"entries": self.entries})
        return entry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record artifact provenance and SHA-256 hashes."
    )
    parser.add_argument("--name", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--file", required=True)
    parser.add_argument("--tier", required=True)
    parser.add_argument("--notes", default="")
    args = parser.parse_args()

    tracker = ProvenanceTracker()
    entry = tracker.record(args.name, args.url, args.file, args.tier, args.notes)
    print(f"Provenance recorded: {entry['file']}")
    print(f"SHA-256: {entry['sha256_hash']}")


if __name__ == "__main__":
    main()
