import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="Map Analysis",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ Wi-Fi Hotspot Map Analysis")
st.markdown(
    "Visualize crowd density and hotspot utilization across the city."
)

# -----------------------------------------------------
# DATABASE CONNECTION
# -----------------------------------------------------
@st.cache_resource
def get_db():
    client = MongoClient(st.secrets["MONGO_URI"])
    return client["wifi_db"]

db = get_db()
collection = db["wifi_sessions"]

# -----------------------------------------------------
# LOAD DATA
# -----------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    data = list(
        collection.find({}, {"_id": 0})
    )

    df = pd.DataFrame(data)

    return df

df = load_data()

if df.empty:
    st.warning("No Wi-Fi data available.")
    st.stop()

# -----------------------------------------------------
# SIDEBAR FILTER
# -----------------------------------------------------
st.sidebar.header("Map Filters")

selected_nodes = st.sidebar.multiselect(
    "Select Wi-Fi Nodes",
    sorted(df["node_id"].unique()),
    default=sorted(df["node_id"].unique())
)

filtered_df = df[
    df["node_id"].isin(selected_nodes)
]

# -----------------------------------------------------
# VERIFY LOCATION COLUMNS
# -----------------------------------------------------
required_cols = [
    "coordinates_lat",
    "coordinates_lon"
]

for col in required_cols:
    if col not in filtered_df.columns:
        st.error(f"Missing column: {col}")
        st.stop()

# -----------------------------------------------------
# CROWD DENSITY AGGREGATION
# -----------------------------------------------------
density_df = (
    filtered_df
    .groupby(
        [
            "node_id",
            "coordinates_lat",
            "coordinates_lon"
        ]
    )
    .agg(
        Total_Sessions=("session_id", "count"),
        Unique_Users=("mac_address_hashed", "nunique"),
        Total_Data=("bytes_transferred", "sum")
    )
    .reset_index()
)

# -----------------------------------------------------
# KPIs
# -----------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric(
    "Total Locations",
    density_df.shape[0]
)

col2.metric(
    "Total Users",
    density_df["Unique_Users"].sum()
)

col3.metric(
    "Total Sessions",
    density_df["Total_Sessions"].sum()
)

st.divider()

# -----------------------------------------------------
# INTERACTIVE MAP
# -----------------------------------------------------
st.subheader("📍 Hotspot Density Map")

fig = px.scatter_mapbox(
    density_df,
    lat="coordinates_lat",
    lon="coordinates_lon",
    size="Unique_Users",
    color="Unique_Users",
    hover_name="node_id",
    hover_data=[
        "Total_Sessions",
        "Unique_Users"
    ],
    zoom=10,
    height=700,
    title="Wi-Fi Crowd Density"
)

fig.update_layout(
    mapbox_style="open-street-map"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# -----------------------------------------------------
# TOP CONGESTED NODES
# -----------------------------------------------------
st.subheader("🔥 Top 10 Congested Wi-Fi Nodes")

top_nodes = (
    density_df
    .sort_values(
        by="Unique_Users",
        ascending=False
    )
    .head(10)
)

fig_bar = px.bar(
    top_nodes,
    x="node_id",
    y="Unique_Users",
    color="Unique_Users",
    text="Unique_Users",
    title="Most Crowded Wi-Fi Nodes"
)

st.plotly_chart(
    fig_bar,
    use_container_width=True
)

# -----------------------------------------------------
# DATA TRANSFER MAP
# -----------------------------------------------------
st.subheader("📡 Data Transfer Analysis")

density_df["Data_GB"] = (
    density_df["Total_Data"] /
    (1024 ** 3)
)

fig_data = px.scatter_mapbox(
    density_df,
    lat="coordinates_lat",
    lon="coordinates_lon",
    size="Data_GB",
    color="Data_GB",
    hover_name="node_id",
    zoom=10,
    height=700,
    title="Data Consumption by Location"
)

fig_data.update_layout(
    mapbox_style="open-street-map"
)

st.plotly_chart(
    fig_data,
    use_container_width=True
)

# -----------------------------------------------------
# NODE TABLE
# -----------------------------------------------------
st.subheader("📋 Location Statistics")

display_df = density_df[
    [
        "node_id",
        "Total_Sessions",
        "Unique_Users",
        "Data_GB"
    ]
]

st.dataframe(
    display_df,
    use_container_width=True
)

# -----------------------------------------------------
# DOWNLOAD DATA
# -----------------------------------------------------
csv = display_df.to_csv(
    index=False
)

st.download_button(
    "⬇ Download Location Statistics",
    csv,
    file_name="wifi_location_statistics.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption(
    "Map Analysis • Public Wi-Fi Hotspot Usage Analyzer"
)
