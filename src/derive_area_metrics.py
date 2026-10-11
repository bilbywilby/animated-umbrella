#!/usr/bin/env python3
"""Generate derived_area_metrics.json for wiki generator."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE: Path = Path("./tmp_onepagers/pa_ra_onepagers")
ds: Dict[str, Any] = json.loads((BASE / "data/pa_ra_dataset.json").read_text())

ind: List[Dict[str, Any]] = ds["individual"]
sg: List[Dict[str, Any]] = ds["small_group"]
areas: Dict[str, List[str]] = ds["areas"]

county_to_area: Dict[str, str] = {c: a for a, cs in areas.items() for c in cs}
assert len(county_to_area) == 67, f"Expected 67 counties, got {len(county_to_area)}"

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
print("CHECKS:", {k: round(v, 2) for k, v in chk.items()})
print("TARGETS: ind27=15.97  sg27=10.28  ind27req=17.14  ind26=21.5")
