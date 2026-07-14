import pandas as pd
import streamlit as st
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data
def load_all():
    env = pd.read_csv(os.path.join(DATA_DIR, "environmental_daily.csv"), parse_dates=["date"])
    op = pd.read_csv(os.path.join(DATA_DIR, "operational_daily.csv"), parse_dates=["date"])
    bins_df = pd.read_csv(os.path.join(DATA_DIR, "smart_bins.csv"), parse_dates=["install_date"])
    trips = pd.read_csv(os.path.join(DATA_DIR, "truck_trip_logs.csv"), parse_dates=["date"])
    trucks = pd.read_csv(os.path.join(DATA_DIR, "trucks.csv"))
    wf = pd.read_csv(os.path.join(DATA_DIR, "workforce.csv"))
    att = pd.read_csv(os.path.join(DATA_DIR, "workforce_attendance.csv"), parse_dates=["date"])

    # enrich trips with truck static info
    trips = trips.merge(trucks, on=["truck_id", "region"], how="left", suffixes=("", "_truck"))
    trips["fuel_efficiency_l_100km"] = (trips["fuel_consumed_l"] / trips["distance_km"].replace(0, pd.NA)) * 100
    trips["load_ton"] = trips["load_kg"] / 1000

    # enrich attendance with worker static info
    att = att.merge(wf, on="worker_id", how="left")

    # enrich operational with bin static info
    op = op.merge(bins_df[["bin_id", "capacity_liters", "primary_waste_type", "latitude", "longitude"]],
                   on="bin_id", how="left")

    return {
        "env": env,
        "op": op,
        "bins": bins_df,
        "trips": trips,
        "trucks": trucks,
        "wf": wf,
        "att": att,
    }


def filter_by_date_region(df, date_col, region_col, date_range, regions):
    mask = (df[date_col] >= pd.Timestamp(date_range[0])) & (df[date_col] <= pd.Timestamp(date_range[1]))
    if region_col in df.columns and regions:
        mask &= df[region_col].isin(regions)
    return df.loc[mask]
