from typing import Dict, List, Optional
import re

from bs4 import BeautifulSoup


def _clean_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned or None


def parse_crosswalk_from_html(
    html_content: str,
) -> List[Dict[str, Optional[str]]]:
    soup = BeautifulSoup(html_content, "html.parser")
    results: List[Dict[str, Optional[str]]] = []

    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        headers = []
        for cell in rows[0].find_all(["th", "td"]):
            text = _clean_text(cell.get_text()) or ""
            headers.append(
                re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
            )

        if not headers:
            continue

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            record = {
                headers[i]: _clean_text(cell.get_text())
                for i, cell in enumerate(cells[:len(headers)])
            }
            if any(record.values()):
                results.append(record)

        if results:
            break

    return results
