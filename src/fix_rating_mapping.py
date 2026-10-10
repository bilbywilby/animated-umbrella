#!/usr/bin/env python3
import json
from pathlib import Path

DATA_FILE = Path("data/pa_rating_areas.json")

def fix_mappings():
    if not DATA_FILE.exists():
        print(f"❌ {DATA_FILE} not found")
        return

    with open(DATA_FILE, "r") as f:
        data = json.load(f)

    # Mapping swap: Area 1 <-> Area 7
    # This aligns the JSON with the CMS crosswalk and Wiki File 7
    mapping = data.get("rating_areas", {})
    
    # Temporary hold to avoid overwriting during swap
    area1_counties = mapping.get("1")
    area7_counties = mapping.get("7")
    
    mapping["1"] = area7_counties
    mapping["7"] = area1_counties
    
    data["rating_areas"] = mapping

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
    
    print("✅ Rating Area 1 and 7 successfully swapped in JSON.")

if __name__ == "__main__":
    fix_mappings()
