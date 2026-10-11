#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Fixed the "file" variable error by using __file__
ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = ROOT / "data"
DATA_PATH: Path = DATA_DIR / "pa_ra_dataset.json"

if not DATA_PATH.exists():
    DATA_PATH = DATA_DIR / "pa_ra_validated_dataset.json"

ds: Dict[str, Any] = json.loads(DATA_PATH.read_text())
ind: List[Dict[str, Any]] = ds["individual"]
raw_2026 = ds.get("individual_2026_only", [])
ind_2026_only: List[Dict[str, Any]] = list(raw_2026.values()) if isinstance(raw_2026, dict) else raw_2026
ind_full: List[Dict[str, Any]] = ind + ind_2026_only
sg: List[Dict[str, Any]] = ds["small_group"]
areas: Dict[str, List[str]] = ds["areas"]
county_to_area: Dict[str, str] = {c: a for a, cs in areas.items() for c in cs}

assert len(county_to_area) == 67, f"Expected 67 counties, got {len(county_to_area)}"

def mix(filers: List[Dict[str, Any]]) -> Optional[float]:
    valid = [f for f in filers if f.get("share26") is not None and f.get("app27") is not None]
    w: float = sum(f["share26"] for f in valid)
    return sum(f["share26"] * f["app27"] for f in valid) / w if w > 0 else None

def area_filers(filers: List[Dict[str, Any]], area: str) -> List[Dict[str, Any]]:
    cs: set[str] = set(areas[area])
    hits: List[Dict[str, Any]] = []
    for f in filers:
        if f.get("app27") is None:
            continue
        fcs = f.get("counties")
        if fcs == "ALL" or (isinstance(fcs, list) and set(fcs) & cs):
            hits.append(f)
    return hits

term = ds.get("terminations_oe2026", {}).get("top20_pct", {})
A: Dict[str, Any] = {}
for a in sorted(areas, key=int):
    fil = area_filers(ind, a)
    onpennie = [f for f in fil if f.get("on_pennie")]
    thin = [c for c in areas[a] if sum(1 for f in onpennie if f.get("counties") == "ALL" or c in f.get("counties", [])) <= 2]
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

ranked = sorted([a for a in A if A[a]["mix_approved"] is not None], key=lambda a: -(A[a]["mix_approved"] or 0))
for i, a in enumerate(ranked, 1):
    A[a]["rank_mix_1_is_highest"] = i

def state_mix(rows: List[Dict[str, Any]], key: str) -> float:
    valid_rows = [r for r in rows if r.get(key) is not None and r.get("share26") is not None]
    total_weight = sum(r["share26"] for r in valid_rows)
    valid_sum = sum(r["share26"] * r[key] for r in valid_rows)
    return valid_sum / total_weight if total_weight > 0 else 0.0

chk = {
    "ind27": state_mix(ind_full, "app27"),
    "sg27": state_mix(sg, "app27"),
    "ind27req": state_mix(ind_full, "req27"),
    "ind26": state_mix(ind_full, "app26"),
}
A["_checks"] = chk
out = DATA_DIR / "derived_area_metrics.json"
out.write_text(json.dumps(A, indent=2) + "\n")
print("CHECKS:", {k: round(v, 2) for k, v in chk.items()})
print("TARGETS: ind27=15.97  sg27=10.28  ind27req=17.14  ind26=21.5")
