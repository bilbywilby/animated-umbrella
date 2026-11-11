#!/usr/bin/env python3
"""src/parse_cms_crosswalk.py - Python 3.14 compatible CMS parser."""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def parse_cms_html(html_file: Path) -> Dict[str, str]:
    """Extract county→area pairs using multiple fallback patterns."""
    content = html_file.read_text(encoding="utf-8")
    mapping: Dict[str, str] = {}
    
    # Pattern 1: "County Name" → Area X
    pattern1 = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Rating\s+)?Area\s+(\d+)\b'
    
    # Pattern 2: Table cells (county in td, area in next td)
    pattern2 = r'<td[^>]*>\s*([^<>]+)\s*</td>\s*<td[^>]*>\s*(\d+)\s*</td>'
    
    # Pattern 3: Data attributes
    pattern3 = r'(county|area)["\']?\s*[:=]\s*["\']?([^"\'>]+)["\']?\s*[:=]\s*["\']?(\d+)'
    
    patterns = [pattern1, pattern2, pattern3]
    excluded = ['county', 'area', 'rating', 'state', 'pennsylvania', 'header']
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if len(match) >= 2:
                county = match[0].strip()
                area = match[-1].strip()
                
                if len(county) > 3 and county.lower() not in excluded:
                    if county not in mapping:  # First pattern wins
                        mapping[county] = str(area)
    
    return mapping


def main() -> int:
    parser = argparse.ArgumentParser(description="Parse CMS PA rating area crosswalk")
    parser.add_argument("--input", required=True, help="Path to cms_crosswalk.html")
    parser.add_argument("--output", default="data/cms_county_to_area.json", help="Output JSON")
    parser.add_argument("--verbose", action="store_true", help="Show extraction stats")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        sys.stderr.write(f"[ERROR] Input file not found: {input_path}\n")
        return 1
    
    try:
        mapping = parse_cms_html(input_path)
        
        if len(mapping) < 60:
            sys.stderr.write(f"[WARN] Only {len(mapping)} counties; expected 67\n")
            if mapping:
                sys.stderr.write(f"[DEBUG] Sample: {list(mapping.items())[:5]}\n")
        else:
            print(f"✅ Extracted {len(mapping)} counties from CMS crosswalk")
        
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps(mapping, indent=2, sort_keys=True) + "\n",
            encoding="utf-8"
        )
        
        print(f"   Output: {args.output}")
        return 0
        
    except Exception as e:
        sys.stderr.write(f"[ERROR] {e}\n")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
