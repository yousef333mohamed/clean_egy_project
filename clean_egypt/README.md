# ♻️ Clean Egypt — Data Analysis Dashboard

A Streamlit dashboard for exploring the Clean Egypt project data (EDA), in a green/white theme.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

The browser will open automatically at `http://localhost:8501`.

## Project structure

```
clean_egypt/
├── app.py                  # Main dashboard code
├── data_loader.py           # Loading & merging the data files
├── requirements.txt
├── .streamlit/config.toml   # Color theme (green/white)
└── data/                    # The seven CSV files
```

## Contents

- **Key Performance Indicators (KPIs)**: fleet/bin/worker scale, total waste collected,
  missed collection rate, complaints, emergencies, attendance, performance, fuel efficiency.
- **Overview**: time trends for waste volume and missed collection by region and day of week.
- **Environment & Impact**: weather (temperature/rainfall) vs. waste volume, effect of
  holidays and traffic, and a correlation matrix.
- **Smart Bins**: distribution by waste type and capacity, plus an interactive bin map.
- **Fleet & Trips**: trip status, fuel efficiency, per-truck performance.
- **Workforce**: attendance, performance, completed tasks by shift, overtime hours.
- **Data Quality**: missing-value summary per file, with a raw data preview.

Date range and Region/Governorate filters live in the sidebar and apply across the whole dashboard.

## Adding new data later

When more files arrive, drop them into the `data/` folder and update `data_loader.py`
to read and merge them with the rest of the tables (via `bin_id`, `truck_id`, `worker_id`,
or `date` + `region`).
