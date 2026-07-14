import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from data_loader import load_all, filter_by_date_region

# ----------------------------------------------------------------------------
# Page config
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Clean Egypt | Waste Management Data Dashboard",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

GREEN_DARK = "#145A32"
GREEN = "#1E8449"
GREEN_MED = "#28B463"
GREEN_LIGHT = "#82E0AA"
GREEN_PALE = "#EAF6EE"
GREY = "#6B7A70"
GREENS_SEQ = ["#145A32", "#1E8449", "#28B463", "#52BE80", "#82E0AA", "#ABEBC6"]

px.defaults.color_discrete_sequence = GREENS_SEQ
px.defaults.template = "plotly_white"

# ----------------------------------------------------------------------------
# Custom CSS — green & white theme
# ----------------------------------------------------------------------------
st.markdown(f"""
<style>
[data-testid="stMetric"] {{
    background-color: #FFFFFF;
    border: 1px solid #d4ecdb;
    border-left: 6px solid {GREEN};
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 4px rgba(20,90,50,0.08);
}}
[data-testid="stMetricLabel"] {{
    color: {GREEN_DARK};
    font-weight: 600;
}}
[data-testid="stMetricValue"] {{
    color: {GREEN_DARK};
}}
[data-testid="stSidebar"] {{
    background-color: {GREEN_PALE};
    border-right: 1px solid #d4ecdb;
}}
h1, h2, h3 {{
    color: {GREEN_DARK};
}}
.section-title {{
    background-color: {GREEN_PALE};
    padding: 8px 14px;
    border-radius: 8px;
    border-left: 5px solid {GREEN};
    margin-top: 6px;
    margin-bottom: 10px;
    font-weight: 700;
    color: {GREEN_DARK};
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: 4px;
}}
.stTabs [data-baseweb="tab"] {{
    background-color: {GREEN_PALE};
    border-radius: 8px 8px 0 0;
    padding: 8px 16px;
    color: {GREEN_DARK};
    font-weight: 600;
}}
.stTabs [aria-selected="true"] {{
    background-color: {GREEN} !important;
    color: white !important;
}}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Load data
# ----------------------------------------------------------------------------
data = load_all()
env, op, bins_df, trips, trucks, wf, att = (
    data["env"], data["op"], data["bins"], data["trips"], data["trucks"], data["wf"], data["att"]
)

MIN_DATE = min(env["date"].min(), op["date"].min(), trips["date"].min(), att["date"].min()).date()
MAX_DATE = max(env["date"].max(), op["date"].max(), trips["date"].max(), att["date"].max()).date()
ALL_REGIONS = sorted(env["region"].unique().tolist())

# ----------------------------------------------------------------------------
# Sidebar — filters
# ----------------------------------------------------------------------------
st.sidebar.markdown("## ♻️ Clean Egypt")
st.sidebar.caption("Data exploration & key performance indicators")
st.sidebar.markdown("---")

date_range = st.sidebar.date_input(
    "Date range",
    value=(MIN_DATE, MAX_DATE),
    min_value=MIN_DATE,
    max_value=MAX_DATE,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = MIN_DATE, MAX_DATE

selected_regions = st.sidebar.multiselect(
    "Region", options=ALL_REGIONS, default=ALL_REGIONS
)
if not selected_regions:
    selected_regions = ALL_REGIONS

selected_govs = st.sidebar.multiselect(
    "Governorate (optional)",
    options=sorted(op["governorate"].unique().tolist()),
    default=[],
)

st.sidebar.markdown("---")
st.sidebar.caption("Dashboard updates automatically as filters change")

# ----------------------------------------------------------------------------
# Apply filters
# ----------------------------------------------------------------------------
f_env = filter_by_date_region(env, "date", "region", (start_date, end_date), selected_regions)
f_op = filter_by_date_region(op, "date", "region", (start_date, end_date), selected_regions)
f_trips = filter_by_date_region(trips, "date", "region", (start_date, end_date), selected_regions)
f_att = filter_by_date_region(att, "date", "region", (start_date, end_date), selected_regions)

if selected_govs:
    f_op = f_op[f_op["governorate"].isin(selected_govs)]
    f_att = f_att[f_att["governorate"].isin(selected_govs)]

f_bins = bins_df[bins_df["region"].isin(selected_regions)]
if selected_govs:
    f_bins = f_bins[f_bins["governorate"].isin(selected_govs)]

f_wf = wf[wf["region"].isin(selected_regions)]
if selected_govs:
    f_wf = f_wf[f_wf["governorate"].isin(selected_govs)]

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.title("♻️ Clean Egypt — Data Analysis Dashboard")
st.caption(
    f"Exploring Egypt's waste management data · {start_date} to {end_date} · "
    f"{len(selected_regions)} of {len(ALL_REGIONS)} regions selected"
)

# ----------------------------------------------------------------------------
# KPI Row 1 — Scale
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">📊 Scale & Coverage</div>', unsafe_allow_html=True)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Smart Bins", f'{f_bins["bin_id"].nunique():,}')
c2.metric("Active Trucks", f'{f_trips["truck_id"].nunique():,}')
c3.metric("Registered Workers", f'{f_wf["worker_id"].nunique():,}')
c4.metric("Governorates Served", f'{f_op["governorate"].nunique():,}')
c5.metric("Days of Data", f'{f_op["date"].nunique():,}')

# ----------------------------------------------------------------------------
# KPI Row 2 — Waste & Collection
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">🚛 Waste Volume & Collection</div>', unsafe_allow_html=True)
completed_trips = f_trips[f_trips["status"] == "Completed"]
total_waste_ton = completed_trips["load_ton"].sum()
avg_daily_waste_ton = completed_trips.groupby("date")["load_ton"].sum().mean() if len(completed_trips) else 0
missed_rate = f_op["missed_collection"].mean() * 100 if len(f_op) else 0
avg_service_time = f_op["service_completion_time_min"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Waste Collected", f'{total_waste_ton:,.0f} tons')
c2.metric("Avg Daily Waste", f'{avg_daily_waste_ton:,.1f} tons/day')
c3.metric("Missed Collection Rate", f'{missed_rate:,.1f}%')
c4.metric("Avg Service Completion Time", f'{avg_service_time:,.1f} min')

# ----------------------------------------------------------------------------
# KPI Row 3 — Operational issues
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">🚨 Operational Issues</div>', unsafe_allow_html=True)
emergency_count = int(f_op["emergency_request"].sum())
complaints_count = int(f_op["complaint_filed"].sum())
dumping_count = int(f_op["illegal_dumping_flag"].sum())
completion_rate = (f_trips["status"] == "Completed").mean() * 100 if len(f_trips) else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Emergency Requests", f'{emergency_count:,}')
c2.metric("Complaints Filed", f'{complaints_count:,}')
c3.metric("Illegal Dumping Incidents", f'{dumping_count:,}')
c4.metric("Trip Completion Rate", f'{completion_rate:,.1f}%')

# ----------------------------------------------------------------------------
# KPI Row 4 — Workforce & Fleet
# ----------------------------------------------------------------------------
st.markdown('<div class="section-title">👷 Workforce & Fleet</div>', unsafe_allow_html=True)
attendance_rate = f_att["present"].mean() * 100 if len(f_att) else 0
avg_performance = f_att["performance_score"].mean()
avg_fuel_eff = completed_trips["fuel_efficiency_l_100km"].mean()
avg_speed = completed_trips["avg_speed_kmh"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Worker Attendance Rate", f'{attendance_rate:,.1f}%')
c2.metric("Avg Performance Score", f'{avg_performance:,.1f}')
c3.metric("Avg Fuel Consumption", f'{avg_fuel_eff:,.1f} L/100km')
c4.metric("Avg Truck Speed", f'{avg_speed:,.1f} km/h')

st.markdown("---")

# ----------------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------------
tab_overview, tab_env, tab_bins, tab_fleet, tab_workforce, tab_quality = st.tabs([
    "📈 Overview", "🌦️ Environment & Impact", "🗑️ Smart Bins",
    "🚛 Fleet & Trips", "👷 Workforce", "🔍 Data Quality"
])

# ============================================================================
# TAB 1 — Overview
# ============================================================================
with tab_overview:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Daily Waste Collected — Trend")
        daily_waste = completed_trips.groupby("date")["load_ton"].sum().reset_index()
        fig = px.area(daily_waste, x="date", y="load_ton",
                       labels={"date": "Date", "load_ton": "Waste (tons)"},
                       color_discrete_sequence=[GREEN_MED])
        fig.update_traces(line_color=GREEN_DARK)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Missed Collection Rate — Trend")
        daily_missed = f_op.groupby("date")["missed_collection"].mean().mul(100).reset_index()
        fig = px.line(daily_missed, x="date", y="missed_collection",
                       labels={"date": "Date", "missed_collection": "Missed Collection Rate (%)"},
                       color_discrete_sequence=[GREEN_DARK])
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Waste Volume by Region")
        waste_by_region = completed_trips.groupby("region")["load_ton"].sum().reset_index().sort_values("load_ton", ascending=True)
        fig = px.bar(waste_by_region, x="load_ton", y="region", orientation="h",
                     labels={"load_ton": "Waste (tons)", "region": "Region"},
                     color="load_ton", color_continuous_scale=GREENS_SEQ)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Avg Daily Waste by Day of Week")
        wt = completed_trips.copy()
        wt["weekday"] = wt["date"].dt.day_name()
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        wk = wt.groupby("weekday")["load_ton"].mean().reindex(order).reset_index()
        fig = px.bar(wk, x="weekday", y="load_ton",
                     labels={"weekday": "Day of Week", "load_ton": "Avg Waste (tons)"},
                     color_discrete_sequence=[GREEN])
        st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 2 — Environmental
# ============================================================================
with tab_env:
    st.subheader("Weather vs. Waste Volume")
    daily_env = f_env.groupby("date").agg(
        temperature_c=("temperature_c", "mean"),
        rainfall_mm=("rainfall_mm", "sum"),
    ).reset_index()
    daily_waste2 = completed_trips.groupby("date")["load_ton"].sum().reset_index()
    merged = daily_env.merge(daily_waste2, on="date", how="inner")

    col1, col2 = st.columns(2)
    with col1:
        fig = px.scatter(merged, x="temperature_c", y="load_ton", trendline="ols",
                          labels={"temperature_c": "Temperature (°C)", "load_ton": "Waste Volume (tons)"},
                          color_discrete_sequence=[GREEN_DARK])
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.scatter(merged, x="rainfall_mm", y="load_ton", trendline="ols",
                          labels={"rainfall_mm": "Rainfall (mm)", "load_ton": "Waste Volume (tons)"},
                          color_discrete_sequence=[GREEN_MED])
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Impact of Holidays & Festivals")
    op_env = f_op.merge(f_env, on=["date", "region"], how="left")
    col3, col4, col5 = st.columns(3)

    with col3:
        g = op_env.groupby("is_weekend")["missed_collection"].mean().mul(100).reset_index()
        g["is_weekend"] = g["is_weekend"].map({True: "Weekend", False: "Weekday"})
        fig = px.bar(g, x="is_weekend", y="missed_collection",
                     labels={"is_weekend": "", "missed_collection": "Missed Collection Rate (%)"},
                     color_discrete_sequence=[GREEN])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Missed collection: weekend vs. weekday")

    with col4:
        g = op_env.groupby("is_holiday")["missed_collection"].mean().mul(100).reset_index()
        g["is_holiday"] = g["is_holiday"].map({True: "Public Holiday", False: "Regular Day"})
        fig = px.bar(g, x="is_holiday", y="missed_collection",
                     labels={"is_holiday": "", "missed_collection": "Missed Collection Rate (%)"},
                     color_discrete_sequence=[GREEN_MED])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Missed collection: public holidays")

    with col5:
        g = op_env.groupby("traffic_level")["service_completion_time_min"].mean().reset_index()
        fig = px.bar(g, x="traffic_level", y="service_completion_time_min",
                     labels={"traffic_level": "Traffic Level", "service_completion_time_min": "Avg Service Time (min)"},
                     category_orders={"traffic_level": ["Low", "Medium", "High"]},
                     color_discrete_sequence=[GREEN_DARK])
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Service time by traffic level")

    st.markdown("---")
    st.subheader("Correlation Matrix — Environmental & Operational Variables")
    corr_df = op_env.copy()
    corr_df["missed_collection"] = corr_df["missed_collection"].astype(int)
    corr_df["emergency_request"] = corr_df["emergency_request"].astype(int)
    corr_df["complaint_filed"] = corr_df["complaint_filed"].astype(int)
    corr_df["illegal_dumping_flag"] = corr_df["illegal_dumping_flag"].astype(int)
    num_cols = ["temperature_c", "rainfall_mm", "missed_collection", "emergency_request",
                "complaint_filed", "illegal_dumping_flag", "service_completion_time_min"]
    corr = corr_df[num_cols].corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=["#FFFFFF", GREEN_MED, GREEN_DARK],
                     labels=dict(color="Correlation"))
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 3 — Smart Bins
# ============================================================================
with tab_bins:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Bins by Waste Type")
        wtype = f_bins["primary_waste_type"].value_counts().reset_index()
        wtype.columns = ["primary_waste_type", "count"]
        fig = px.pie(wtype, names="primary_waste_type", values="count", hole=0.45,
                     color_discrete_sequence=GREENS_SEQ)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Bins by Capacity (Liters)")
        cap = f_bins["capacity_liters"].value_counts().reset_index()
        cap.columns = ["capacity_liters", "count"]
        cap = cap.sort_values("capacity_liters")
        fig = px.bar(cap, x="capacity_liters", y="count",
                     labels={"capacity_liters": "Capacity (L)", "count": "Number of Bins"},
                     color_discrete_sequence=[GREEN])
        fig.update_xaxes(type="category")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Smart Bins Map")
    if len(f_bins) and f_bins["latitude"].notna().any():
        fig = px.scatter_map(
            f_bins.dropna(subset=["latitude", "longitude"]),
            lat="latitude", lon="longitude", color="region",
            hover_name="bin_id", hover_data=["governorate", "primary_waste_type", "capacity_liters"],
            zoom=4.5, height=520, color_discrete_sequence=GREENS_SEQ,
        )
        fig.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No coordinates available for the current filter selection.")

    st.markdown("---")
    st.subheader("Number of Bins by Governorate")
    gov_count = f_bins["governorate"].value_counts().reset_index()
    gov_count.columns = ["governorate", "count"]
    gov_count = gov_count.sort_values("count", ascending=True)
    fig = px.bar(gov_count, x="count", y="governorate", orientation="h",
                 labels={"count": "Number of Bins", "governorate": "Governorate"},
                 color="count", color_continuous_scale=GREENS_SEQ, height=650)
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 4 — Fleet & trips
# ============================================================================
with tab_fleet:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Trip Status")
        status_count = f_trips["status"].value_counts().reset_index()
        status_count.columns = ["status", "count"]
        fig = px.pie(status_count, names="status", values="count", hole=0.45,
                     color_discrete_sequence=GREENS_SEQ)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Avg Fuel Consumption by Fuel Type")
        fe = f_trips[f_trips["status"] == "Completed"].groupby("fuel_type")["fuel_efficiency_l_100km"].mean().reset_index()
        fig = px.bar(fe, x="fuel_type", y="fuel_efficiency_l_100km",
                     labels={"fuel_type": "Fuel Type", "fuel_efficiency_l_100km": "L / 100km"},
                     color_discrete_sequence=[GREEN_DARK, GREEN_LIGHT])
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Distance vs. Fuel Consumed")
        fig = px.scatter(completed_trips, x="distance_km", y="fuel_consumed_l", color="fuel_type",
                          labels={"distance_km": "Distance (km)", "fuel_consumed_l": "Fuel Consumed (L)", "fuel_type": "Fuel Type"},
                          color_discrete_sequence=[GREEN_DARK, GREEN_LIGHT], opacity=0.6)
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Truck Performance (Avg Load per Trip)")
        truck_perf = completed_trips.groupby("truck_id")["load_kg"].mean().reset_index().sort_values("load_kg", ascending=True)
        fig = px.bar(truck_perf, x="load_kg", y="truck_id", orientation="h",
                     labels={"load_kg": "Avg Load (kg)", "truck_id": "Truck"},
                     color="load_kg", color_continuous_scale=GREENS_SEQ, height=500)
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Daily Distance Driven & Stops Completed")
    daily_trip = completed_trips.groupby("date").agg(
        distance_km=("distance_km", "sum"),
        stops_completed=("stops_completed", "sum"),
    ).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily_trip["date"], y=daily_trip["distance_km"], name="Distance (km)",
                              line=dict(color=GREEN_DARK)))
    fig.add_trace(go.Scatter(x=daily_trip["date"], y=daily_trip["stops_completed"], name="Stops Completed",
                              yaxis="y2", line=dict(color=GREEN_LIGHT)))
    fig.update_layout(
        yaxis=dict(title="Distance (km)"),
        yaxis2=dict(title="Stops Completed", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1),
        template="plotly_white",
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 5 — Workforce
# ============================================================================
with tab_workforce:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Daily Attendance Rate — Trend")
        daily_att = f_att.groupby("date")["present"].mean().mul(100).reset_index()
        fig = px.line(daily_att, x="date", y="present",
                       labels={"date": "Date", "present": "Attendance Rate (%)"},
                       color_discrete_sequence=[GREEN_DARK])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Performance Score Distribution")
        fig = px.histogram(f_att.dropna(subset=["performance_score"]), x="performance_score", nbins=30,
                            labels={"performance_score": "Performance Score"},
                            color_discrete_sequence=[GREEN])
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Avg Completed Tasks by Shift")
        shift_perf = f_att.groupby("shift")["completed_tasks"].mean().reset_index()
        fig = px.bar(shift_perf, x="shift", y="completed_tasks",
                     labels={"shift": "Shift", "completed_tasks": "Avg Completed Tasks"},
                     color_discrete_sequence=[GREEN_MED])
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.subheader("Experience Years vs. Performance Score")
        fig = px.scatter(f_att.dropna(subset=["performance_score"]), x="experience_years", y="performance_score",
                          trendline="ols", color_discrete_sequence=[GREEN_DARK],
                          labels={"experience_years": "Experience (years)", "performance_score": "Performance Score"})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Overtime Hours by Governorate")
    ot = f_att.groupby("governorate")["overtime_hours"].sum().reset_index().sort_values("overtime_hours", ascending=True)
    fig = px.bar(ot, x="overtime_hours", y="governorate", orientation="h",
                 labels={"overtime_hours": "Total Overtime Hours", "governorate": "Governorate"},
                 color="overtime_hours", color_continuous_scale=GREENS_SEQ, height=650)
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 6 — Data quality
# ============================================================================
with tab_quality:
    st.subheader("Data Quality Overview (Missing Values)")
    datasets = {
        "environmental_daily": env, "operational_daily": op, "smart_bins": bins_df,
        "truck_trip_logs": trips, "trucks": trucks, "workforce": wf, "workforce_attendance": att,
    }
    rows = []
    for name, df in datasets.items():
        rows.append({
            "File": name,
            "Rows": len(df),
            "Columns": df.shape[1],
            "Missing Values (%)": round(df.isna().mean().mean() * 100, 2),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("Missing Values by Column")
    chosen = st.selectbox("Select a dataset", options=list(datasets.keys()))
    df_sel = datasets[chosen]
    miss = df_sel.isna().sum().reset_index()
    miss.columns = ["Column", "Missing Values"]
    miss["Percent (%)"] = (miss["Missing Values"] / len(df_sel) * 100).round(2)
    miss = miss.sort_values("Missing Values", ascending=False)
    fig = px.bar(miss, x="Missing Values", y="Column", orientation="h",
                 color_discrete_sequence=[GREEN])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Raw Data Preview")
    st.dataframe(df_sel.head(200), use_container_width=True)

st.markdown("---")
st.caption("Clean Egypt · Waste Management Data Dashboard — built with Claude")
