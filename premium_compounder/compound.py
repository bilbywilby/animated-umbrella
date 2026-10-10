#!/usr/bin/env python3
"""
Carl's Premium Compounding Engine
Designed for Bilbywilby to calculate multi-year ACA premium impacts.
Uses Decimal for financial precision to avoid floating-point drift.
"""

import argparse
import sys
from decimal import Decimal, ROUND_HALF_UP
from typing import List

def calculate_compounded_impact(initial_premium: Decimal, rates: List[Decimal]):
    """
    Computes the premium progression over a series of annual rate changes.
    Returns a list of (year, premium) tuples and the total percentage increase.
    """
    results = []
    current_premium = initial_premium
    
    for year, rate in enumerate(rates, start=1):
        # Formula: New = Old * (1 + rate/100)
        multiplier = Decimal('1') + (rate / Decimal('100'))
        current_premium = (current_premium * multiplier).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        results.append((year, current_premium))
    
    total_pct_increase = ((current_premium / initial_premium) - Decimal('1')) * Decimal('100')
    return results, total_pct_increase

def main():
    parser = argparse.ArgumentParser(
        description="Compute compounded health insurance premium impacts over multiple years."
    )
    parser.add_argument(
        "--base", 
        type=float, 
        required=True, 
        help="The starting monthly premium (e.g., 450.00)"
    )
    parser.add_argument(
        "--rates", 
        type=float, 
        nargs="+", 
        required=True, 
        help="Annual percentage increases (e.g., 15.97 12.5 8.0)"
    )
    
    args = parser.parse_args()

    try:
        # Convert inputs to Decimal for precision
        base_premium = Decimal(str(args.base))
        if base_premium <= 0:
            raise ValueError("Base premium must be a positive number. Quack!")
            
        annual_rates = [Decimal(str(r)) for r in args.rates]
        
        results, total_pct = calculate_compounded_impact(base_premium, annual_rates)
        
        # Output Formatting
        print("\n--- 🦆 Carl's Premium Impact Report ---")
        print(f"Starting Monthly Premium: ${base_premium:,.2f}")
        print("-" * 35)
        print(f"{'Year':<8} | {'Rate':<10} | {'Premium':<12}")
        print("-" * 35)
        
        for i, (year, premium) in enumerate(results):
            rate = annual_rates[i]
            print(f"{year:<8} | {rate:>8.2f}% | ${premium:>11,.2f}")
            
        print("-" * 35)
        print(f"Final Monthly Premium:   ${results[-1][1]:,.2f}")
        print(f"Total Compounded Hike:   {total_pct:.2f}%")
        print("------------------------------------\n")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
