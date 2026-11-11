import json
import sys
from decimal import Decimal, ROUND_HALF_UP

def load_data():
    with open("market_data.json", "r") as f:
        return json.load(f)

def ascii_bar(value, max_val, width=20):
    filled = int((value / max_val) * width)
    return "█" * filled + "░" * (width - filled)

def run_audit(data, current_premium=None, filter_min=None):
    carriers = data["carriers"]
    max_rate = max(c["approved"] for c in carriers)
    
    print("\n--- 🦆 PA ACA 2027 RISK POOL VISUALIZATION ---")
    print(f"{'Carrier':<35} | {'Approved %':<12} | {'Relative Impact'}")
    print("-" * 75)
    
    for c in carriers:
        if filter_min and c["approved"] < filter_min:
            continue
            
        bar = ascii_bar(c["approved"], max_rate)
        print(f"{c['name']:<35} | {c['approved']:>10.2f}% | {bar}")
    
    if current_premium:
        print("\n--- 🦆 INTERACTIVE RATE CALCULATOR ---")
        prem = Decimal(str(current_premium))
        print(f"Current Monthly Base: ${prem:,.2f}")
        print("-" * 40)
        for c in carriers:
            multiplier = Decimal('1') + (Decimal(str(c["approved"])) / Decimal('100'))
            new_prem = (prem * multiplier).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            print(f"{c['name'][:25]:<25} -> ${new_prem:>10,.2f} (+{c['approved']:.2f}%)")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--premium", type=float, help="Current monthly premium for calculation")
    parser.add_argument("--min", type=float, help="Filter carriers by minimum approved rate")
    args = parser.parse_args()
    
    try:
        data = load_data()
        run_audit(data, args.premium, args.min)
    except FileNotFoundError:
        print("Error: market_data.json not found. Run extractor.py first! Quack!")

if __name__ == "__main__":
    main()
