#!/usr/bin/env python3
import json
import sys
from datetime import datetime
from typing import Dict, List

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def analyze_swings(prev: List[Dict], curr: List[Dict], threshold: float = 10.0):
    swings = {}
    prev_map = {item['carrier_name']: item for item in prev}
    
    for item in curr:
        name = item['carrier_name']
        if name in prev_map:
            p_prev = prev_map[name]['premium_usd']
            p_curr = item['premium_usd']
            
            if p_prev > 0:
                diff = abs((p_curr - p_prev) / p_prev) * 100
                if diff > threshold:
                    swings[name] = {
                        'premium_change': diff,
                        'prev_val': p_prev,
                        'curr_val': p_curr
                    }
    return swings

def main():
    try:
        prev = load_json('data/pa_ra_dataset_2026.json')
        curr = load_json('data/pa_ra_dataset_2027.json')
    except FileNotFoundError as e:
        print(f"Error: Missing dataset for comparison: {e}")
        sys.exit(1)

    swings = analyze_swings(prev, curr)
    print(f"--- Delta Report {datetime.now().isoformat()} ---")
    if not swings:
        print("No volatility exceeding threshold detected.")
    else:
        for carrier, data in swings.items():
            print(f"ALERT: {carrier} | Premium Swing: {data['premium_change']:.2f}%")

if __name__ == "__main__":
    main()
