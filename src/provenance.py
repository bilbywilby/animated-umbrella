#!/usr/bin/env python3
"""Provenance Tracker – records artifact metadata and optional SHA‑256 hash.

Usage example:
  python -m src.provenance \\
    --name "PY2027 Dataset" \\
    --url "https://www.pid.state.pa.us" \\
    --file data/pa_ra_dataset.json \\
    --tier VERIFIED \\
    --checksum
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import hashlib
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

# ----------------------------------------------------------------------
# Helper: atomic write (re‑uses the original implementation)
# ----------------------------------------------------------------------
def atomic_write_json(destination: Path, payload: Mapping[str, Any]) -> None:
    """Write *payload* to *destination* atomically.

    The file is first written to a temporary sibling file, flushed,
    then renamed over the target.  This guarantees readers never see a
    partially‑written JSON document.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_path, destination)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise

# ----------------------------------------------------------------------
# Dataclass representing a provenance entry
# ----------------------------------------------------------------------
@dataclass(slots=True)
class ProvenanceEntry:
    name: str               # Human‑readable identifier for the artefact
    url: str                # Source URL (redacted by ctx.sh later)
    file: str               # Relative path to the artefact
    tier: str               # Verification tier, e.g. VERIFIED / UNVERIFIED
    notes: str = ""         # Optional free‑form notes
    checksum: str | None = None  # SHA‑256 hex digest (optional)
    timestamp_utc: str = datetime.now(timezone.utc).isoformat()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON‑serialisable mapping, omitting None values."""
        d = asdict(self)
        # Remove keys with value None to keep the JSON tidy
        return {k: v for k, v in d.items() if v is not None}


# ----------------------------------------------------------------------
# Provenance tracker – manages a JSON log file
# ----------------------------------------------------------------------
class ProvenanceTracker:
    """Collects provenance entries in a JSON log file.

    The default location is ``data/provenance/audit_log.json``.  If the
    file already exists, entries are loaded and appended to.
    """

    def __init__(self, log_file: Path = Path("data/provenance/audit_log.json")) -> None:
        self.log_file = log_file
        self.entries: list[ProvenanceEntry] = []
        if self.log_file.exists():
            try:
                with self.log_file.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                for raw in data.get("entries", []):
                    # Defensive: ignore malformed rows
                    if isinstance(raw, dict):
                        self.entries.append(ProvenanceEntry(**raw))
            except (json.JSONDecodeError, OSError):
                # Corrupt log – start fresh but emit a warning
                sys.stderr.write(f"[WARN] Corrupt log ignored: {self.log_file}\n")

    def record(
        self,
        name: str,
        url: str,
        file_path: str,
        tier: str,
        notes: str = "",
        checksum: str | None = None,
    ) -> ProvenanceEntry:
        """Create a new entry, append it, and persist the log."""
        entry = ProvenanceEntry(
            name=name,
            url=url,
            file=file_path,
            tier=tier,
            notes=notes,
            checksum=checksum,
        )
        self.entries.append(entry)
        # Serialise the whole list under a top‑level ``entries`` key
        atomic_write_json(
            self.log_file, {"entries": [e.as_dict() for e in self.entries]}
        )
        return entry


# ----------------------------------------------------------------------
# Utility: compute SHA‑256 checksum of a file (optionally streamed)
# ----------------------------------------------------------------------
def compute_sha256(path: Path) -> str:
    """Return the hex‑digest of *path*'s SHA‑256 hash."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    # Truncate to the first 12 characters for readability, matching ctx.sh
    return h.hexdigest()[:12]


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Record artifact provenance and optional SHA‑256 hash."
    )
    parser.add_argument("--name", required=True, help="Name of the source / dataset")
    parser.add_argument(
        "--url", required=True, help="Source URL (will be redacted downstream)"
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Relative path to the artefact that is being recorded",
    )
    parser.add_argument(
        "--tier",
        required=True,
        help="Verification tier (e.g. VERIFIED, UNVERIFIED, MANUAL)",
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional free‑form notes attached to the entry",
    )
    parser.add_argument(
        "--checksum",
        action="store_true",
        help="Compute and store a truncated SHA‑256 checksum of the file",
    )
    return parser


def main() -> int:
    args = build_argparser().parse_args()

    # Resolve the file path relative to the repository root
    file_path = Path(args.file)
    if not file_path.is_file():
        sys.stderr.write(f"[ERROR] File not found: {file_path}\n")
        return 1

    checksum = compute_sha256(file_path) if args.checksum else None

    tracker = ProvenanceTracker()
    entry = tracker.record(
        name=args.name,
        url=args.url,
        file_path=str(file_path),
        tier=args.tier,
        notes=args.notes,
        checksum=checksum,
    )
    # Human‑readable confirmation (ctx.sh will capture the stdout)
    print(f"✅ Provenance recorded for {entry.file}")
    if checksum:
        print(f"   checksum (truncated) = {checksum}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
