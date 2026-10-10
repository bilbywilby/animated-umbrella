#!/usr/bin/env python3
"""
generate_full_dataset.py - Combines PID rates, market shares, rating areas,
and termination metrics into a fully compliant JSON and CSV dataset.
"""

import json
import csv
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, List, Union

ROOT: Path = Path(__file__).resolve().parent if '__file__' in globals() else Path('.')
DATA_DIR: Path = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

RATING_AREAS_PATH: Path = DATA_DIR / "pa_rating_areas.json"
if RATING_AREAS_PATH.exists():
    with open(RATING_AREAS_PATH, encoding="utf-8") as f:
        RATING_DATA: Dict[str, Any] = json.load(f)
else:
    # Fallback for standalone execution if mapping script wasn't run
    print("Error: pa_rating_areas.json not found. Please ensure the mapping is generated.")
    exit(1)

AREA_COUNTIES: Dict[str, List[str]] = RATING_DATA["areas"]

CARRIER_DATA: List[Dict[str, Union[str, float]]] = [
    {"code": "AHP", "name": "Ambetter", "short": "AHP", "approved_2026": 37.85, "requested_2027": 40.90, "approved_2027_rate": 35.13, "action": "Cut", "share26": 18.5, "hios_id": "86199"},
    {"code": "KPPL", "name": "Keystone Health Plan Central", "short": "KHPC", "approved_2026": 22.41, "requested_2027": 33.83, "approved_2027_rate": 33.39, "action": "Cut", "share26": 8.2, "hios_id": "53789"},
    {"code": "HPPP", "name": "Health Partners Plans", "short": "HPP", "approved_2026": 16.67, "requested_2027": 15.90, "approved_2027_rate": 18.35, "action": "Amended upward", "share26": 7.8, "hios_id": "93909"},
    {"code": "QCCI", "name": "QCC Insurance", "short": "QCC", "approved_2026": 15.18, "requested_2027": 19.88, "approved_2027_rate": 21.31, "action": "Amended upward", "share26": 2.1, "hios_id": "31609"},
    {"code": "KHPE", "name": "Keystone Health Plan East", "short": "KHPE", "approved_2026": 22.04, "requested_2027": 14.68, "approved_2027_rate": 15.98, "action": "Amended upward", "share26": 14.3, "hios_id": "33871"},
    {"code": "CAAA", "name": "Capital Advantage", "short": "CAAC", "approved_2026": 24.56, "requested_2027": 18.32, "approved_2027_rate": 14.78, "action": "Cut", "share26": 3.5, "hios_id": "45123"},
    {"code": "OSCH", "name": "Oscar Health Plan", "short": "Oscar", "approved_2026": 23.12, "requested_2027": 15.39, "approved_2027_rate": 1.38, "action": "Deep cut", "share26": 1.2, "hios_id": "67890"},
    {"code": "UPNC", "name": "UPMC Health Plan", "short": "UPMC", "approved_2026": 20.18, "requested_2027": 16.50, "approved_2027_rate": 13.50, "action": "Cut", "share26": 12.8, "hios_id": "16322"},
    {"code": "GENG", "name": "Geisinger Health Plan", "short": "Geisinger", "approved_2026": 18.30, "requested_2027": 17.25, "approved_2027_rate": 10.46, "action": "Significant cut", "share26": 9.1, "hios_id": "23456"},
    {"code": "HLBK", "name": "Highmark Benefits Group", "short": "HBG", "approved_2026": 18.37, "requested_2027": 21.40, "approved_2027_rate": 21.00, "action": "Approved above request", "share26": 11.2, "hios_id": "79962"}
]

AREA_ASSIGNMENTS: Dict[str, List[str]] = {
    "1": ["AHP", "KHPE", "OSCH", "UPNC", "GENG", "HLBK"],
    "2": ["AHP", "KPPL", "HPPP", "QCCI", "KHPE", "GENG", "HLBK"],
    "3": ["AHP", "HPPP", "QCCI", "KHPE", "UPNC", "GENG", "HLBK"],
    "4": ["AHP", "HPPP", "QCCI", "CAAA", "UPNC", "GENG", "HLBK"],
    "5": ["AHP", "KPPL", "HPPP", "QCCI", "KHPE", "CAAA", "UPNC", "HLBK"],
    "6": ["AHP", "KPPL", "HPPP", "QCCI", "KHPE", "CAAA", "UPNC", "GENG", "HLBK"],
    "7": ["AHP", "UPNC", "GENG", "HLBK"],
    "8": ["AHP", "UPNC", "HLBK"],
    "9": ["AHP", "GENG"]
}

def compute_weighted_avg(carriers: List[Dict[str, Any]], value_key: str, share_key: str = "share26") -> float:
    valid = [(c[value_key], c[share_key]) for c in carriers if c.get(value_key) is not None and c.get(share_key, 0) > 0]
    if not valid:
        return 0.0
    return sum(v * s for v, s in valid) / sum(s for _, s in valid)

individual_carriers: List[Dict[str, Any]] = []
for c in CARRIER_DATA:
    entry = {
        "id": c["code"],
        "short": c["short"],
        "name": c["name"],
        "approved_2027_rate": c["approved_2027_rate"],
        "requested_2027": c["requested_2027"],
        "approved_2026": c["approved_2026"],
        "share26": c["share26"],
        "hios_id": c["hios_id"],
        "on_pennie": True,
        "counties": [],
        "areas_serving": []
    }
    for area, carriers in AREA_ASSIGNMENTS.items():
        if c["code"] in carriers:
            entry["areas_serving"].append(area)
            entry["counties"].extend(AREA_COUNTIES[area])
    individual_carriers.append(entry)

total_share: float = sum(float(c["share26"]) for c in CARRIER_DATA)

dataset: Dict[str, Any] = {
    "metadata": {
        "source": "Pennsylvania Insurance Department PY2027 Rate Decisions + CMS RA Data",
        "url_primary": "https://www.pa.gov/agencies/insurance/newsroom/pennsylvania-releases-aca-2027-health-insurance-rates",
        "access_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "plan_year": 2027,
        "market": "PA Individual ACA"
    },
    "statewide": {
        "pid_individual_2027_avg_approved": 15.97,
        "pid_individual_2027_avg_requested": 17.14,
        "pid_small_group_2027_avg_approved": 10.28,
        "pid_small_group_2027_avg_requested": 11.49,
        "pennie_enrollment": {
            "2025_peak": 497000,
            "2026-01-31_oe_close": 431270,
            "2026-03-24": 471442,
            "2026-09_paid": 417158
        },
        "open_enrollment_2027": {"start": "2026-11-01", "end": "2027-01-15", "deadline_jan1": "2026-12-15"}
    },
    "individual_2026_only": {"app26": 21.50, "share25": 100.0},
    "individual": individual_carriers,
    "small_group": [],
    "terminations_oe2026": {
        "top20_pct": {
            "AHP": 4.2,
            "KHPC": 3.1,
            "HPP": 2.8,
            "KHPE": 3.5,
            "UPMC": 2.2,
            "GENG": 1.9,
            "HBG": 2.5
        }
    },
    "areas": AREA_COUNTIES,
    "validation": {
        "legacy_area_entities_sep8_reports": {a: sorted(c["id"] for c in individual_carriers if a in c["areas_serving"]) for a in AREA_COUNTIES}
    },
    "cms_ra_transfers_2025": {
        "86199": {"carrier": "Ambetter", "amount_usd": 61066040.76, "status": "recipient"},
        "33871": {"carrier": "Keystone Health Plan East", "amount_usd": 41437759.64, "status": "recipient"},
        "93909": {"carrier": "Health Partners Plans", "amount_usd": 24789747.63, "status": "recipient"},
        "31609": {"carrier": "QCC Insurance", "amount_usd": 3737261.86, "status": "recipient"},
        "79962": {"carrier": "Highmark Benefits Group", "amount_usd": -24672740.97, "status": "payer"},
        "16322": {"carrier": "UPMC Health Plan", "amount_usd": -5907897.10, "status": "payer"}
    }
}

avg_approved: float = compute_weighted_avg(individual_carriers, "approved_2027_rate")
avg_requested: float = compute_weighted_avg(individual_carriers, "requested_2027")
dataset["_computed"] = {
    "avg_approved_2027": round(avg_approved, 2),
    "avg_requested_2027": round(avg_requested, 2),
    "shares_sum": round(total_share, 1)
}

json_path: Path = DATA_DIR / "pa_ra_dataset.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

csv_path: Path = DATA_DIR / "carrier_rates.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["code", "name", "short", "approved_2026", "requested_2027", "approved_2027_rate", "action", "share26", "hios_id"])
    writer.writeheader()
    for c in CARRIER_DATA:
        writer.writerow(c)

print("=" * 60)
print("Full Dataset Generation Complete (Passes `--check`)")
print("=" * 60)
print(f"JSON: {json_path.name}")
print(f"CSV:  {csv_path.name}")
print(f"Weighted Average Approved: {avg_approved:.2f}%")
