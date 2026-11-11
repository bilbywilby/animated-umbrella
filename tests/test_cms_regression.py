import hashlib
import json
from pathlib import Path

import pytest

# Import your existing parser – adjust the import path if needed
from src.cms_parser import parse_crosswalk_from_html  # <-- replace with real function name


@pytest.fixture(scope="session")
def baseline_checksum() -> str:
    """Checksum of the canonical JSON generated from the baseline HTML."""
    baseline_html = Path("tests/fixtures/baseline_2027.html")
    parsed = parse_crosswalk_from_html(str(baseline_html))
    # Normalise to a deterministic string (sorted keys)
    normalized = json.dumps(parsed, sort_keys=True).encode()
    return hashlib.sha256(normalized).hexdigest()


def test_cms_crosswalk_regression(baseline_checksum: str):
    """Fail the build if the parser output deviates from the baseline checksum."""
    current_html = Path("cms_crosswalk.html")
    assert current_html.is_file(), "Fetch step must produce cms_crosswalk.html first"

    parsed = parse_crosswalk_from_html(str(current_html))
    normalized = json.dumps(parsed, sort_keys=True).encode()
    current_checksum = hashlib.sha256(normalized).hexdigest()

    assert (
        current_checksum == baseline_checksum
    ), f"CMS parser output changed (got {current_checksum}, expected {baseline_checksum})"
