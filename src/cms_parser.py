#!/usr/bin/env python3
\"\"\"CMS crosswalk parser for rate review data.\"\"\"
from pathlib import Path
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

def parse_crosswalk_from_html(html_content: str) -> List[Dict[str, Any]]:
    \"\"\"Parse issuer crosswalk tables from CMS HTML filings.\"\"\"
    soup = BeautifulSoup(html_content, \"html.parser\")
    rows: List[Dict[str, Any]] = []
    
    table = soup.find(\"table\")
    if not table:
        return rows
        
    for tr in table.find_all(\"tr\")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all([\"td\", \"th\"])]
        if len(cols) >= 3:
            rows.append({
                \"issuer\": cols[0],
                \"hios_id\": cols[1],
                \"successor\": cols[2] if len(cols) > 2 else None
            })
    return rows
