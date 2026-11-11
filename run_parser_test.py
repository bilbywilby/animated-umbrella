from pathlib import Path
from src.cms_parser import parse_crosswalk_from_html
import json

def run_test():
    raw_html_path = Path("data/raw_crosswalk.html")
    if raw_html_path.exists():
        html_data = raw_html_path.read_text(encoding="utf-8")
        crosswalk_records = parse_crosswalk_from_html(html_data)
        print(f"Successfully extracted {len(crosswalk_records)} records from production data.")
        if crosswalk_records:
            print("Sample Record Keys:", list(crosswalk_records[0].keys()))
            print("Sample Data:", json.dumps(crosswalk_records[0], indent=2))
    else:
        print(f"Error: Target data file not found at {raw_html_path}")
        print("Please place your HTML file in data/raw_crosswalk.html")

if __name__ == "__main__":
    run_test()
