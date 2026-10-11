#!/usr/bin/env python3
"""Generate derived_area_metrics.json for wiki generator."""
import json
from pathlib import Path

BASE = Path("./tmp_onepagers/pa_ra_onepagers")
ds = json.loads((BASE / "data/pa_ra_dataset.json").read_text())

ind, sg, areas = ds["individual"], ds["small_group"], ds["areas"]
county_to_area = {c: a for a, cs in areas.items() for c in cs}
assert len(county_to_area) == 67, f"Expected 67 counties, got {len(county_to_area)}"

def mix(filers):
    w = sum(f["share26"] for f in filers)
    return sum(f["share26"] * f["app27"] for f in filers) / w if w else None

def area_filers(filers, area):
    cs = set(areas[area])
    hits = []
    for f in filers:
        if f.get("app27") is None: continue
        fcs = f["counties"]
        if fcs == "ALL" or (isinstance(fcs, list) and set(fcs) & cs):
            hits.append(f)
    return hits

term = ds["terminations_oe2026"]["top20_pct"]
A = {}
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

def state_mix(rows, key):
    return sum(r["share26"] * r[key] for r in rows if r.get(key)) / sum(r["share26"] for r in rows if r.get(key))

chk = {
    "ind27": state_mix(ind, "app27"),
    "sg27": state_mix(sg, "app27"),
    "ind27req": state_mix(ind, "req27"),
    "ind26": state_mix([r for r in ind if r.get("app26")], "app26"),
}
A["_checks"] = chk
out = BASE / "data/derived_area_metrics.json"
out.write_text(json.dumps(A, indent=2) + "\n")
print("CHECKS:", {k: round(v, 2) for k, v in chk.items()})
print("TARGETS: ind27=15.97  sg27=10.28  ind27req=17.14  ind26=21.5")
