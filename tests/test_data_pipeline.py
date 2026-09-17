import io
import json
from pathlib import Path

import pandas as pd

import src.data as data_module
from src import official_data
from src.data import create_sample_data, load_dashboard_data


def test_create_sample_data_has_expected_columns():
    df = create_sample_data(rows=12, seed=7)

    assert len(df) == 12
    assert {
        "date",
        "region",
        "crop",
        "rainfall_mm",
        "temperature_c",
        "soil_quality",
        "yield_tonnes_per_hectare",
        "market_price_inr",
    }.issubset(df.columns)


def test_create_sample_data_includes_all_regions_and_crops():
    df = create_sample_data(rows=768, seed=17)

    assert set(df["region"]) == {
        "Punjab",
        "Maharashtra",
        "Karnataka",
        "West Bengal",
        "Andhra Pradesh",
        "Tamil Nadu",
        "Uttar Pradesh",
        "Haryana",
    }
    assert set(df["crop"]) == {
        "Rice",
        "Wheat",
        "Cotton",
        "Maize",
        "Sugarcane",
        "Soybean",
        "Mustard",
        "Groundnut",
    }


def test_load_dashboard_data_reads_project_root_file(tmp_path, monkeypatch):
    project_root = tmp_path / "project-root"
    official_dir = project_root / "data" / "processed"
    official_dir.mkdir(parents=True)
    official_csv = official_dir / "agriculture.csv"
    pd.DataFrame(
        [{
            "date": "2024-01-01",
            "region": "Punjab",
            "crop": "Rice",
            "rainfall_mm": 100.0,
            "temperature_c": 26.0,
            "soil_quality": 70.0,
            "yield_tonnes_per_hectare": 3.5,
            "market_price_inr": 2300,
        }]
    ).to_csv(official_csv, index=False)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(data_module, "PROJECT_ROOT", project_root)

    df, using_official = load_dashboard_data()

    assert using_official is True
    assert list(df.columns) == [
        "date",
        "region",
        "crop",
        "rainfall_mm",
        "temperature_c",
        "soil_quality",
        "yield_tonnes_per_hectare",
        "market_price_inr",
    ]


def test_download_data_gov_resource_writes_csv(monkeypatch, tmp_path):
    payload = {"records": [{"region": "Punjab", "crop": "Rice", "value": 42}]}

    class FakeResponse(io.StringIO):
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            self.close()

    def fake_urlopen(request, timeout=60):
        return FakeResponse(json.dumps(payload))

    monkeypatch.setattr(official_data, "urlopen", fake_urlopen)

    df = official_data.download_data_gov_resource(
        api_key="abc123",
        resource_id="res-1",
        output_path=tmp_path / "downloaded" / "official.csv",
        limit=50,
    )

    assert list(df.columns) == ["region", "crop", "value"]
    assert (tmp_path / "downloaded" / "official.csv").exists()


def test_load_dashboard_data_auto_fetches_and_cleans_official_data(monkeypatch, tmp_path):
    project_root = tmp_path / "project-root"
    project_root.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DATA_GOV_API_KEY", "abc123")
    monkeypatch.setenv("DATA_GOV_RESOURCE_ID", "res-1")
    monkeypatch.setattr(data_module, "PROJECT_ROOT", project_root)

    raw_path = project_root / "data" / "raw" / "official.csv"
    raw_path.parent.mkdir(parents=True)

    raw_df = pd.DataFrame(
        [{
            "State": "Punjab",
            "Crop": "Rice",
            "Date": "2024-01-01",
            "Rainfall (mm)": 120.0,
            "Temperature (C)": 26.0,
            "Soil Quality": 72.0,
            "Yield (t/ha)": 3.8,
            "Price (INR)": 2400,
        }]
    )
    raw_df.to_csv(raw_path, index=False)

    def fake_download(api_key, resource_id, output_path, limit=10000):
        assert api_key == "abc123"
        assert resource_id == "res-1"
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        raw_df.to_csv(output, index=False)
        return raw_df

    monkeypatch.setattr(data_module.official_data, "download_data_gov_resource", fake_download)

    df, using_official = load_dashboard_data()

    assert using_official is True
    assert list(df.columns) == [
        "date",
        "region",
        "crop",
        "rainfall_mm",
        "temperature_c",
        "soil_quality",
        "yield_tonnes_per_hectare",
        "market_price_inr",
    ]
    assert df.iloc[0]["region"] == "Punjab"
