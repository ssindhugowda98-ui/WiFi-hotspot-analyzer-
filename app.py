import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------
st.set_page_config(
    page_title="Public Wi-Fi Hotspot Usage Analyzer",
    page_icon="📶",
    layout="wide"
)

# --------------------------------------------------
# MongoDB Connection
# --------------------------------------------------
@st.cache_resource
def get_database():
    client = MongoClient(st.secrets["MONGO_URI"])
    return client["wifi_db"]

db = get_database()
collection = db["wifi_sessions"]

# --------------------------------------------------
# Load Data
# --------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.DataFrame(data)

    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df

df = load_data()

# --------------------------------------------------
# Header
# --------------------------------------------------
st.title("📶 Public Wi-Fi Hotspot Usage Analyzer")
st.markdown(
    """
    Analyze Wi-Fi hotspot traffic, crowd density,
    peak hours, and network utilization.
    """
)

# --------------------------------------------------
# No Data Check
# --------------------------------------------------
if df.empty:
    st.warning("No data found in MongoDB.")
    st.stop()

# --------------------------------------------------
# KPI Metrics
# --------------------------------------------------
total_sessions = len(df)

total_users = df["mac_address_hashed"].nunique()

total_nodes = df["node_id"].nunique()

avg_duration = round(
    df["connection_duration_secs"].mean() / 60,
    2
)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Sessions", f"{total_sessions:,}")
col2.metric("Unique Users", f"{total_users:,}")
col3.metric("Wi-Fi Nodes", f"{total_nodes:,}")
col4.metric("Avg Duration (min)", avg_duration)

st.divider()

# --------------------------------------------------
# Hourly Usage
# --------------------------------------------------
st.subheader("📈 Hourly Connection Trends")

df["hour"] = df["timestamp"].dt.hour

hourly = (
    df.groupby("hour")
    .size()
    .reset_index(name="connections")
)

fig_hour = px.line(
    hourly,
    x="hour",
    y="connections",
    markers=True,
    title="Connections by Hour"
)

st.plotly_chart(fig_hour, use_container_width=True)

# --------------------------------------------------
# Top Wi-Fi Nodes
# --------------------------------------------------
st.subheader("🏆 Top 10 Busy Wi-Fi Nodes")

node_usage = (
    df.groupby("node_id")
    .size()
    .reset_index(name="sessions")
    .sort_values(
        by="sessions",
        ascending=False
    )
    .head(10)
)

fig_nodes = px.bar(
    node_usage,
    x="node_id",
    y="sessions",
    text="sessions",
    title="Top 10 Wi-Fi Nodes"
)

st.plotly_chart(fig_nodes, use_container_width=True)

# --------------------------------------------------
# Data Usage
# --------------------------------------------------
st.subheader("📊 Data Consumption Distribution")

fig_data = px.histogram(
    df,
    x="bytes_transferred",
    nbins=50,
    title="Bytes Transferred Distribution"
)

st.plotly_chart(fig_data, use_container_width=True)

# --------------------------------------------------
# Map Visualization
# --------------------------------------------------
st.subheader("🗺️ Hotspot Activity Map")

if "coordinates_lat" in df.columns and "coordinates_lon" in df.columns:

    map_df = (
        df.groupby(
            ["coordinates_lat", "coordinates_lon"]
        )
        .size()
        .reset_index(name="connections")
    )

    fig_map = px.scatter_mapbox(
        map_df,
        lat="coordinates_lat",
        lon="coordinates_lon",
        size="connections",
        color="connections",
        zoom=10,
        height=600,
        title="Wi-Fi Crowd Density"
    )

    fig_map.update_layout(
        mapbox_style="open-street-map"
    )

    st.plotly_chart(
        fig_map,
        use_container_width=True
    )

# --------------------------------------------------
# Raw Data
# --------------------------------------------------
with st.expander("View Dataset"):
    st.dataframe(df, use_container_width=True)

# --------------------------------------------------
# Footer
# --------------------------------------------------
st.markdown("---")
st.caption(
    "Public Wi-Fi Hotspot Usage Analyzer | MongoDB + Streamlit + Plotly"
)
