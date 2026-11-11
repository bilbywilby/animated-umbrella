#!/usr/bin/env python3
"""Reconcile old vs. new rating area mappings and validate coverage."""

import json
import sys
from pathlib import Path
from typing import Mapping

def main() -> int:
    old_mapping_file = Path("data/pa_rating_areas.json")
    new_mapping_file = Path("cms_county_to_area.json")
    
    if not new_mapping_file.exists():
        sys.stderr.write(f"[ERROR] {new_mapping_file} not found. Run parse_cms_crosswalk.py first.\n")
        return 1
    
    with old_mapping_file.open() as f:
        old = json.load(f)
    with new_mapping_file.open() as f:
        new = json.load(f)
    
    print("=== RATING AREA RECONCILIATION ===\n")
    
    # Find counties in old but not in new
    removed = set(old.keys()) - set(new.keys())
    if removed:
        print(f"❌ Removed from CMS (should not happen): {sorted(removed)}")
    
    # Find counties in new but not in old
    added = set(new.keys()) - set(old.keys())
    if added:
        print(f"⚠️  Added in CMS: {sorted(added)}")
    
    # Find re-assignments (same county, different area)
    reassigned = {c: (old[c], new[c]) for c in (set(old) & set(new)) if old[c] != new[c]}
    if reassigned:
        print(f"\n❌ RE-ASSIGNED COUNTIES (data will change):")
        for county, (old_area, new_area) in sorted(reassigned.items()):
            print(f"   {county}: Area {old_area} → Area {new_area}")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Old mapping: {len(old)} counties in {len(set(old.values()))} areas")
    print(f"New mapping: {len(new)} counties in {len(set(new.values()))} areas")
    print(f"Coverage: {len(set(old) & set(new))}/{len(old)} counties match")
    
    if reassigned or removed:
        print("\n⚠️  CRITICAL: Dataset will change. Review before proceeding.")
        return 1
    else:
        print("\n✅ No breaking changes detected.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
