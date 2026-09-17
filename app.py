from __future__ import annotations

import plotly.express as px
import streamlit as st

from src.data import load_dashboard_data


st.set_page_config(page_title="AgriIntelligence", page_icon="🌾", layout="wide")

st.title("AgriIntelligence")
st.caption("Agriculture data, made easier to understand")

with st.sidebar:
    st.header("Dashboard filters")
    data, using_official_data = load_dashboard_data()
    selected_regions = st.multiselect(
        "Regions",
        options=sorted(data["region"].unique()),
        default=sorted(data["region"].unique()),
    )
    selected_crops = st.multiselect(
        "Crops",
        options=sorted(data["crop"].unique()),
        default=sorted(data["crop"].unique()),
    )

filtered = data[data["region"].isin(selected_regions) & data["crop"].isin(selected_crops)]

if using_official_data:
    st.success("Using official data from data.gov.in")
else:
    st.info("Using sample data. Add data/processed/agriculture.csv to use downloaded official data.")

if filtered.empty:
    st.warning("Select at least one region and one crop to view the dashboard.")
    st.stop()

metric_columns = st.columns(4)
metric_columns[0].metric("Records", f"{len(filtered):,}")
metric_columns[1].metric("Average yield", f"{filtered['yield_tonnes_per_hectare'].mean():.2f} t/ha")
metric_columns[2].metric("Average price", f"INR {filtered['market_price_inr'].mean():,.0f}")
metric_columns[3].metric("Average rainfall", f"{filtered['rainfall_mm'].mean():.1f} mm")

left_chart, right_chart = st.columns(2)

with left_chart:
    st.subheader("Yield and rainfall")
    yield_chart = px.scatter(
        filtered,
        x="rainfall_mm",
        y="yield_tonnes_per_hectare",
        color="crop",
        hover_data=["region", "date"],
        labels={"rainfall_mm": "Rainfall (mm)", "yield_tonnes_per_hectare": "Yield (tonnes/hectare)"},
    )
    st.plotly_chart(yield_chart, use_container_width=True)

with right_chart:
    st.subheader("Market price over time")
    price_chart = px.line(
        filtered.sort_values("date"),
        x="date",
        y="market_price_inr",
        color="crop",
        labels={"date": "Month", "market_price_inr": "Market price (INR)"},
    )
    st.plotly_chart(price_chart, use_container_width=True)

st.subheader("Filtered data")
st.dataframe(filtered, use_container_width=True, hide_index=True)
