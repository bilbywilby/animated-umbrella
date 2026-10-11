#!/usr/bin/env python3
"""src/tasks.py - Type-safe pipeline orchestration (replaces shell scripts)."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).parent.parent.resolve()

def run_cmd(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run command with structured error handling."""
    result = subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.strip())
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed: {' '.join(args)}", file=sys.stderr)
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)
        sys.exit(result.returncode)
    return result


def step(name: str) -> None:
    """Print step marker."""
    print(f"\n{'='*60}")
    print(f"=== STEP: {name} ===")
    print('='*60)


def pipeline_full() -> None:
    """Execute complete data pipeline."""
    step("Fetch CMS Crosswalk")
    crosswalk_html = ROOT / "cms_crosswalk.html"
    url = "https://www.cms.gov/cciio/programs-and-initiatives/health-insurance-market-reforms/pa-gra"
    run_cmd(["curl", "-sL", url, "-o", str(crosswalk_html)])

    if crosswalk_html.stat().st_size == 0:
        raise RuntimeError("Downloaded crosswalk HTML is empty.")

    step("Parse CMS Crosswalk")
    run_cmd([
        "python3", "src/parse_cms_crosswalk.py",
        "--input", "cms_crosswalk.html",
        "--output", "data/cms_county_to_area.json"
    ])

    step("Generate Full Datasets")
    run_cmd(["python3", "src/generate_full_dataset.py"])

    step("Build Briefings")
    run_cmd(["python3", "src/build_one_pagers.py", "--check"])

    step("Record Provenance")
    run_cmd([
        "python3", "src/provenance.py",
        "--name", "PY2027 Audit Dataset",
        "--url", url,
        "--file", "data/pa_ra_dataset.json",
        "--tier", "VERIFIED",
        "--emit-handover"
    ])

    step("Citation Triage")
    run_cmd(["python3", "src/citation_triage.py", "pa_aca_briefing_py2027_final.html"])

    print(f"\n{'='*60}")
    print("✅ PIPELINE COMPLETED SUCCESSFULLY")
    print('='*60)


def main() -> None:
    parser = argparse.ArgumentParser(description="PA ACA Rate Audit Pipeline Runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    subparsers.add_parser("run", help="Execute full data pipeline")
    subparsers.add_parser("clean", help="Remove generated artifacts")

    args = parser.parse_args()

    if args.command == "run":
        try:
            pipeline_full()
        except Exception as exc:
            print(f"[FATAL] {exc}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "clean":
        print("Cleaning generated artifacts...")
        for pattern in ["*.html", "*.json", "*.pdf", "data/"]:
            run_cmd(["find", ".", "-name", pattern, "-delete"], check=False)
        print("✅ Cleanup complete")


if __name__ == "__main__":
    main()
