#!/usr/bin/env python3
"""Dependency-free Pennsylvania ACA rate audit and scenario calculator."""

import argparse
import csv
import json
import sys

# Approved 2027 Pennsylvania individual-market carrier rates, in percent.
# Statewide averages below are reported aggregate figures, not carrier averages.
CARRIERS = [
    {"carrier": "Ambetter Health of Pennsylvania Inc", "requested_pct": 40.9, "approved_pct": 35.1},
    {"carrier": "Capital Advantage Assurance Company", "requested_pct": 18.3, "approved_pct": 14.8},
    {"carrier": "Geisinger Health Plan", "requested_pct": 10.5, "approved_pct": 8.6},
    {"carrier": "Geisinger Quality Options", "requested_pct": 13.0, "approved_pct": 10.7},
    {"carrier": "Health Partners Plans Inc", "requested_pct": 15.9, "approved_pct": 18.3},
    {"carrier": "Highmark Benefits Group", "requested_pct": 21.4, "approved_pct": 19.7},
    {"carrier": "Highmark Inc", "requested_pct": 16.2, "approved_pct": 14.5},
    {"carrier": "Keystone Health Plan Central", "requested_pct": 33.8, "approved_pct": 33.4},
    {"carrier": "Keystone Health Plan East", "requested_pct": 14.7, "approved_pct": 16.0},
    {"carrier": "Oscar Health Plan of PA", "requested_pct": 15.4, "approved_pct": 1.4},
    {"carrier": "Partners Insurance Company Inc", "requested_pct": 20.5, "approved_pct": 18.8},
    {"carrier": "QCC Insurance Company", "requested_pct": 19.9, "approved_pct": 21.3},
    {"carrier": "UPMC Health Network Inc", "requested_pct": 12.0, "approved_pct": 9.7},
    {"carrier": "UPMC Health Plan Inc", "requested_pct": 15.8, "approved_pct": 13.5},
]

STATEWIDE = {
    "individual_approved_weighted_pct": 15.97,
    "small_group_approved_weighted_pct": 10.28,
    "individual_requested_weighted_pct": 17.14,
    "small_group_requested_weighted_pct": 11.49,
}


def load_carriers(path):
    if not path:
        return CARRIERS
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    required = {"carrier", "requested_pct", "approved_pct"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError(
            "CSV must have headers: carrier,requested_pct,approved_pct"
        )
    return [
        {
            "carrier": row["carrier"],
            "requested_pct": float(row["requested_pct"]),
            "approved_pct": float(row["approved_pct"]),
        }
        for row in rows
    ]


def summary(rows):
    print("Pennsylvania ACA 2027 — approved statewide weighted averages")
    print(f"Individual market: {STATEWIDE['individual_approved_weighted_pct']:.2f}% "
          f"(requested {STATEWIDE['individual_requested_weighted_pct']:.2f}%)")
    print(f"Small group market: {STATEWIDE['small_group_approved_weighted_pct']:.2f}% "
          f"(requested {STATEWIDE['small_group_requested_weighted_pct']:.2f}%)")
    print(f"\nIndividual-market carrier records: {len(rows)}")
    print("Carrier | Requested | Approved | Change vs request")
    for row in rows:
        delta = row["approved_pct"] - row["requested_pct"]
        print(f"{row['carrier']} | {row['requested_pct']:.1f}% | "
              f"{row['approved_pct']:.1f}% | {delta:+.1f} pp")


def carriers(rows, minimum):
    selected = sorted(
        (r for r in rows if r["approved_pct"] >= minimum),
        key=lambda r: r["approved_pct"],
        reverse=True,
    )
    print("Carrier | Requested | Approved | Change vs request")
    for row in selected:
        delta = row["approved_pct"] - row["requested_pct"]
        print(f"{row['carrier']} | {row['requested_pct']:.1f}% | "
              f"{row['approved_pct']:.1f}% | {delta:+.1f} pp")


def compound(base, rates):
    premium = base
    print(f"Starting premium: ${premium:.2f}/month")
    for year, rate in enumerate(rates, start=1):
        premium *= 1 + rate / 100
        print(f"After year {year} at {rate:g}%: ${premium:.2f}/month")
    print(f"Total change: {((premium / base) - 1) * 100:.2f}%")


def attrition(enrollees, annual_drop, years):
    remaining = enrollees
    print(f"Starting enrollment: {remaining:,.0f}")
    for year in range(1, years + 1):
        remaining *= 1 - annual_drop / 100
        print(f"After year {year} at {annual_drop:g}% attrition: {remaining:,.0f}")


def self_test():
    assert len(CARRIERS) == 14
    assert abs(STATEWIDE["individual_approved_weighted_pct"] - 15.97) < 1e-9
    assert abs(100 * 1.1 * 1.1 - 121) < 1e-9
    print("Self-test passed.")


def main():
    argv = sys.argv[1:] or ["summary"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", help="Use a CSV instead of built-in carrier data")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary", help="Show statewide figures and carrier rates")
    p = sub.add_parser("carriers", help="Filter carriers by approved rate")
    p.add_argument("--min-approved", type=float, default=0.0,
                   help="Minimum approved increase, percent")
    p = sub.add_parser("compound", help="Project compounded premium changes")
    p.add_argument("--base", type=float, required=True, help="Starting monthly premium")
    p.add_argument("--rates", type=float, nargs="+", required=True,
                   help="One percentage increase per year")
    p = sub.add_parser("attrition", help="Project enrollment under annual attrition")
    p.add_argument("--enrollees", type=float, required=True)
    p.add_argument("--annual-drop", type=float, required=True, help="Annual drop, percent")
    p.add_argument("--years", type=int, required=True)
    sub.add_parser("self-test", help="Run built-in sanity checks")

    args = parser.parse_args(argv)
    if args.command == "self-test":
        self_test()
        return
    rows = load_carriers(args.csv)
    if args.command == "summary":
        summary(rows)
    elif args.command == "carriers":
        carriers(rows, args.min_approved)
    elif args.command == "compound":
        if args.base <= 0:
            parser.error("--base must be greater than zero")
        compound(args.base, args.rates)
    elif args.command == "attrition":
        if args.enrollees < 0 or not 0 <= args.annual_drop <= 100 or args.years < 0:
            parser.error("enrollees/years must be nonnegative; annual-drop must be 0–100")
        attrition(args.enrollees, args.annual_drop, args.years)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
