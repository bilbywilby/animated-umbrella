#!/usr/bin/env python3
"""CMS crosswalk parser for rate review data."""
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import re

def _clean_text(text: Optional[str]) -> Optional[str]:
    """Normalizes whitespace and strips extraneous characters from scraped cell values."""
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else None

def parse_crosswalk_from_html(html_content: str) -> List[Dict[str, Optional[str]]]:
    """
    Parses real-world CMS or state insurance department issuer crosswalk tables 
    from raw HTML strings, dynamically mapping headers and handling sparse cells.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    
    if not tables:
        return []
        
    results: List[Dict[str, Optional[str]]] = []
    
    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
            
        # Extract and normalize table headers into snake_case keys
        header_row = rows[0]
        headers: List[str] = []
        for th in header_row.find_all(["th", "td"]):
            header_text = _clean_text(th.get_text()) or ""
            norm_key = re.sub(r"[^a-z0-9]+", "_", header_text.lower()).strip("_")
            headers.append(norm_key)
            
        if not headers:
            continue
            
        # Iterate over data rows and map columns to normalized header keys
        for row in rows[1:]:
            cols = row.find_all(["td", "th"])
            if not cols:
                continue
                
            record: Dict[str, Optional[str]] = {}
            for idx, col in enumerate(cols):
                if idx >= len(headers):
                    break
                key = headers[idx]
                val = _clean_text(col.get_text())
                record[key] = val if val else None
                
            # Filter out entirely empty rows
            if any(record.values()):
                results.append(record)
                
        if results:
            break
            
    return results
