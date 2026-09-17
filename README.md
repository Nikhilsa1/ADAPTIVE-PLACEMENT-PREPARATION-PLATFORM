# AgriIntelligence

AgriIntelligence is a beginner-friendly agriculture analytics project. It combines crop yield, weather, and market-price information to support data-driven decisions.

## First milestone

The dashboard currently uses generated sample data so that it can run without downloading external files. We will replace the sample data with real data in the next milestone.

## Run the project

Open a terminal in this folder and run:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown by Streamlit, usually `http://localhost:8501`.

## Project structure

- `app.py`: Streamlit user interface and dashboard logic.
- `src/data.py`: Creates the sample agriculture dataset.
- `src/official_data.py`: Downloads records from a data.gov.in API resource.
- `requirements.txt`: Python libraries used by the project.
- `data/`: Future location for raw and cleaned datasets.

## Download an official dataset

1. Create an account on [data.gov.in](https://www.data.gov.in/) and request an API key.
2. Choose a dataset, open its `Data API` section, and copy its resource ID.
3. Set the credentials in your shell before running the fetch:

```powershell
$env:DATA_GOV_API_KEY = "YOUR_API_KEY"
$env:DATA_GOV_RESOURCE_ID = "RESOURCE_ID"
```

4. Run the automatic fetch-and-clean step:

```powershell
python -c "from src.data import download_and_prepare_official_data; download_and_prepare_official_data()"
```

This downloads the raw dataset to `data/raw/official.csv` and saves the cleaned dashboard version to
`data/processed/agriculture.csv`. The dashboard automatically uses that file when it exists.

Useful official starting points:

- Crop production: [District-wise, season-wise crop production statistics from 1997](https://www.data.gov.in/resource/district-wise-season-wise-crop-production-statistics-1997)
- Weather: [All India area weighted rainfall](https://www.data.gov.in/resource/all-india-area-weighted-monthly-seasonal-and-annual-rainfall-mm)
- Prices: [Current daily mandi prices](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi)

## Learning path

1. Understand the generated dataset and dashboard charts.
2. Add CSV upload support.
3. Clean and combine yield, weather, and market data.
4. Add exploratory data analysis.
5. Train and evaluate yield and price prediction models.
6. Deploy the dashboard.
