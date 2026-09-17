from __future__ import annotations

import os
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src import official_data

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_sample_data(rows: int = 960, seed: int = 42) -> pd.DataFrame:
    """Create realistic sample agriculture records across a broad set of regions and crops."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-01", periods=rows, freq="MS")
    regions = rng.choice(
        [
            "Punjab",
            "Maharashtra",
            "Karnataka",
            "West Bengal",
            "Andhra Pradesh",
            "Tamil Nadu",
            "Uttar Pradesh",
            "Haryana",
        ],
        rows,
    )
    crops = rng.choice(
        ["Rice", "Wheat", "Cotton", "Maize", "Sugarcane", "Soybean", "Mustard", "Groundnut"],
        rows,
    )
    rainfall = rng.normal(105, 32, rows).clip(20, 220)
    temperature = rng.normal(27, 4, rows).clip(16, 40)
    soil_quality = rng.normal(68, 14, rows).clip(25, 98)
    yield_value = (
        2.1
        + soil_quality * 0.018
        + rainfall * 0.004
        - abs(temperature - 25) * 0.08
        + rng.normal(0, 0.35, rows)
    ).clip(0.5, 6.5)
    price = (1900 + yield_value * 180 + rng.normal(0, 260, rows)).clip(900, 4200)

    return pd.DataFrame(
        {
            "date": dates,
            "region": regions,
            "crop": crops,
            "rainfall_mm": rainfall.round(1),
            "temperature_c": temperature.round(1),
            "soil_quality": soil_quality.round(1),
            "yield_tonnes_per_hectare": yield_value.round(2),
            "market_price_inr": price.round(0),
        }
    )


def clean_raw_agriculture_data(raw_path: str | Path, output_path: str | Path) -> pd.DataFrame:
    """Standardize raw downloaded records into the dashboard schema."""
    raw_file = Path(raw_path)
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw agriculture file not found: {raw_file}")

    data = pd.read_csv(raw_file)
    if data.empty:
        raise ValueError("The downloaded dataset is empty.")

    normalized_columns = []
    for column in data.columns:
        cleaned = str(column).strip().lower()
        cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
        cleaned = cleaned.strip("_")
        normalized_columns.append(cleaned)
    data.columns = normalized_columns

    rename_map = {
        "state": "region",
        "district": "region",
        "crop_name": "crop",
        "commodity": "crop",
        "crop": "crop",
        "rainfall_mm": "rainfall_mm",
        "rainfall": "rainfall_mm",
        "temperature_c": "temperature_c",
        "temperature": "temperature_c",
        "soil_quality": "soil_quality",
        "soil": "soil_quality",
        "yield_tonnes_per_hectare": "yield_tonnes_per_hectare",
        "yield": "yield_tonnes_per_hectare",
        "yield_t_ha": "yield_tonnes_per_hectare",
        "yield_tonnes_per_ha": "yield_tonnes_per_hectare",
        "market_price_inr": "market_price_inr",
        "price": "market_price_inr",
        "price_inr": "market_price_inr",
        "date": "date",
        "month": "date",
        "season": "date",
    }
    data = data.rename(columns=rename_map)

    for column in ["date", "region", "crop"]:
        if column not in data.columns:
            for candidate in ["month", "season", "commodity_name"]:
                if candidate in data.columns:
                    data = data.rename(columns={candidate: column})
                    break

    required = [
        "date",
        "region",
        "crop",
        "rainfall_mm",
        "temperature_c",
        "soil_quality",
        "yield_tonnes_per_hectare",
        "market_price_inr",
    ]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Missing columns after cleaning: {missing}")

    cleaned = data[required].copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["region"] = cleaned["region"].astype(str).str.strip().str.title()
    cleaned["crop"] = cleaned["crop"].astype(str).str.strip().str.title()

    for column in ["rainfall_mm", "temperature_c", "soil_quality", "yield_tonnes_per_hectare", "market_price_inr"]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")

    cleaned = cleaned.dropna(subset=["date", "region", "crop"]).reset_index(drop=True)

    target = Path(output_path)
    if not target.is_absolute():
        target = PROJECT_ROOT / target
    target.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(target, index=False)
    return cleaned


def download_and_prepare_official_data(
    api_key: str | None = None,
    resource_id: str | None = None,
    raw_path: str | Path | None = None,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Download the raw official dataset, clean it, and save the processed agriculture CSV."""
    api_key = api_key or os.getenv("DATA_GOV_API_KEY")
    resource_id = resource_id or os.getenv("DATA_GOV_RESOURCE_ID")
    raw_path = Path(raw_path) if raw_path is not None else PROJECT_ROOT / "data" / "raw" / "official.csv"
    output_path = Path(output_path) if output_path is not None else PROJECT_ROOT / "data" / "processed" / "agriculture.csv"

    if not api_key:
        raise ValueError("Set DATA_GOV_API_KEY or pass api_key to download_and_prepare_official_data().")
    if not resource_id:
        raise ValueError("Set DATA_GOV_RESOURCE_ID or pass resource_id to download_and_prepare_official_data().")

    official_data.download_data_gov_resource(api_key, resource_id, raw_path, limit=10000)
    return clean_raw_agriculture_data(raw_path, output_path)


def load_dashboard_data() -> tuple[pd.DataFrame, bool]:
    """Load the cleaned official file when available; otherwise fetch and clean it or fall back to sample data."""
    official_path = PROJECT_ROOT / "data" / "processed" / "agriculture.csv"
    if official_path.exists():
        return pd.read_csv(official_path, parse_dates=["date"]), True

    api_key = os.getenv("DATA_GOV_API_KEY")
    resource_id = os.getenv("DATA_GOV_RESOURCE_ID")
    raw_path = PROJECT_ROOT / "data" / "raw" / "official.csv"

    if api_key and resource_id:
        try:
            official_data.download_data_gov_resource(api_key, resource_id, raw_path, limit=10000)
            cleaned = clean_raw_agriculture_data(raw_path, official_path)
            return cleaned, True
        except Exception:
            return create_sample_data(), False

    return create_sample_data(), False
