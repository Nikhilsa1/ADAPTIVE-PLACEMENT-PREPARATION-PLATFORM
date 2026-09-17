from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def download_data_gov_resource(
    api_key: str,
    resource_id: str,
    output_path: str | Path,
    limit: int = 10000,
) -> pd.DataFrame:
    """Download records from a data.gov.in resource and save them as CSV."""
    if not api_key or api_key == "YOUR_API_KEY":
        raise ValueError("Provide the API key from your data.gov.in account.")
    if not resource_id:
        raise ValueError("Provide the resource ID from the dataset's API page.")

    query = urlencode({"api-key": api_key, "format": "json", "limit": limit})
    url = f"https://api.data.gov.in/resource/{resource_id}?{query}"
    request = Request(url, headers={"User-Agent": "AgriIntelligence/1.0"})
    with urlopen(request, timeout=60) as response:
        payload = json.load(response)

    records = payload.get("records") or payload.get("result") or payload.get("data") or []
    if not records:
        raise ValueError("The API returned no records. Check the resource ID and API key.")

    data = pd.DataFrame(records)
    output = Path(output_path)
    if not output.is_absolute():
        output = PROJECT_ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False)
    return data