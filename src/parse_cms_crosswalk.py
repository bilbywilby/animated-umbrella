#!/usr/bin/env python3
"""Parse CMS PA rating area crosswalk HTML and extract county→area mapping."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import dict

def parse_cms_html(html_file: Path) -> dict[str, str]:
    """Extract county→area from CMS crosswalk HTML.
    
    Returns: {"county_name": "area_number", ...}
    Raises: ValueError if parsing fails.
    """
    with html_file.open("r", encoding="utf-8") as f:
        text = f.read()
    
    # Regex pattern: look for county names + area assignments
    # Adjust based on actual CMS HTML structure
    pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Rating\s+)?Area\s+(\d+)'
    matches = re.findall(pattern, text)
    
    if not matches:
        raise ValueError("No county→area pairs found; verify HTML structure")
    
    mapping = {county: str(area) for county, area in matches}
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse CMS PA rating area crosswalk")
    parser.add_argument("--input", required=True, help="Path to cms_crosswalk.html")
    parser.add_argument("--output", default="cms_county_to_area.json", help="Output JSON")
    args = parser.parse_args()
    
    try:
        mapping = parse_cms_html(Path(args.input))
        Path(args.output).write_text(json.dumps(mapping, indent=2, sort_keys=True))
        print(f"✅ Extracted {len(mapping)} counties from CMS crosswalk")
        print(f"   Output: {args.output}")
        return 0
    except Exception as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
