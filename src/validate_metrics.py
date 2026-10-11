#!/usr/bin/env python3
import subprocess
import json
import sys

TARGETS = {
    "ind27": 15.97,
    "sg27": 10.28,
    "ind27req": 17.14,
    "ind26": 21.5
}
TOLERANCE = 0.01

def main():
    # Execute the derive script and capture output
    res = subprocess.run(["python3", "src/derive_area_metrics.py"], capture_output=True, text=True)
    
    # Extract the JSON result line
    for line in res.stdout.splitlines():
        if line.startswith("RESULT_JSON:"):
            actual = json.loads(line.replace("RESULT_JSON: ", ""))
            
            all_pass = True
            for k, target in TARGETS.items():
                val = actual.get(k, 0)
                diff = abs(val - target)
                status = "✅" if diff <= TOLERANCE else "❌"
                if diff > TOLERANCE: all_pass = False
                print(f"{status} {k}: Actual={val:.2f}, Target={target:.2f} (Diff={diff:.4f})")
            
            if not all_pass:
                print("\n[!] VALIDATION FAILURE: Metrics deviate from targets.")
                sys.exit(1)
            print("\n[+] VALIDATION SUCCESS: All metrics within tolerance.")
            return

    print("[!] Failed to parse RESULT_JSON from derivation engine.")
    sys.exit(1)

if __name__ == "__main__":
    main()
