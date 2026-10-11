#!/usr/bin/env python3
"""Generate derived_area_metrics.json for wiki generator.
Hardened Version: Carter"""
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Resolve BASE relative to script location to prevent CWD crashes
BASE: Path = Path(__file__).resolve().parents[1] / "tmp_onepagers/pa_ra_onepagers"

try:
    ds: Dict[str, Any] = json.loads((BASE / "data/pa_ra_dataset.json").read_text())
except FileNotFoundError:
    print(f"[!] CRITICAL: Dataset not found at {BASE / 'data/pa_ra_dataset.json'}")
    sys.exit(1)

ind: List[Dict[str, Any]] = ds["individual"]
sg: List[Dict[str, Any]] = ds["small_group"]
areas: Dict[str, List[str]] = ds["areas"]

county_to_area: Dict[str, str] = {c: a for a, cs in areas.items() for c in cs}
if len(county_to_area) != 67:
    print(f"[!] DATA INTEGRITY ERROR: Expected 67 counties, found {len(county_to_area)}.")
    # Diagnostic: Identify missing or extra counties here if necessary
    sys.exit(1)

def mix(filers: List[Dict[str, Any]]) -> Optional[float]:
    w: float = sum(f["share26"] for f in filers)
    return sum(f["share26"] * f["app27"] for f in filers) / w if w > 0 else None

def area_filers(filers: List[Dict[str, Any]], area: str) -> List[Dict[str, Any]]:
    cs: set[str] = set(areas[area])
    hits: List[Dict[str, Any]] = []
    for f in filers:
        if f.get("app27") is None:
            continue
        fcs = f["counties"]
        if fcs == "ALL" or (isinstance(fcs, list) and set(fcs) & cs):
            hits.append(f)
    return hits

term: Dict[str, float] = ds["terminations_oe2026"]["top20_pct"]
A: Dict[str, Any] = {}

for a in sorted(areas, key=int):
    fil = area_filers(ind, a)
    onpennie = [f for f in fil if f.get("on_pennie")]
    thin = [c for c in areas[a] if sum(1 for f in onpennie if f["counties"] == "ALL" or c in f["counties"]) <= 2]
    sgfil = area_filers(sg, a)
    A[a] = {
        "counties": areas[a],
        "n_counties": len(areas[a]),
        "individual_filers": fil,
        "n_listed": len(fil),
        "n_on_pennie": len(onpennie),
        "mix_approved": mix(fil),
        "thin_counties": thin,
        "terminations_top20": {c: term[c] for c in areas[a] if c in term},
        "sg_filers": sgfil,
        "sg_mix_approved": mix(sgfil),
    }

ranked = sorted(A, key=lambda a: -(A[a]["mix_approved"] or 0))
for i, a in enumerate(ranked, 1):
    A[a]["rank_mix_1_is_highest"] = i

def state_mix(rows: List[Dict[str, Any]], key: str, total_universe: Optional[List[Dict[str, Any]]] = None) -> float:
    universe = total_universe if total_universe is not None else rows
    total_weight = sum(r["share26"] for r in universe)
    valid_sum = sum(r["share26"] * r[key] for r in rows if r.get(key) is not None)
    return valid_sum / total_weight if total_weight > 0 else 0.0

chk = {
    "ind27": state_mix([r for r in ind if r.get("app27") is not None], "app27", total_universe=ind),
    "sg27": state_mix([r for r in sg if r.get("app27") is not None], "app27", total_universe=sg),
    "ind27req": state_mix([r for r in ind if r.get("req27") is not None], "req27", total_universe=ind),
    "ind26": state_mix([r for r in ind if r.get("app26") is not None], "app26", total_universe=ind),
}
A["_checks"] = chk
out = BASE / "data/derived_area_metrics.json"
out.write_text(json.dumps(A, indent=2) + "\n")

# Output formatted for the validator script
print(f"RESULT_JSON: {json.dumps({k: round(v, 4) for k, v in chk.items()})}")
