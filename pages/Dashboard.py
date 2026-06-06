import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------
st.set_page_config(
    page_title="Wi-Fi Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Wi-Fi Usage Dashboard")

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------
@st.cache_resource
def get_db():
    client = MongoClient(st.secrets["MONGO_URI"])
    return client["wifi_db"]

db = get_db()
collection = db["wifi_sessions"]

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
@st.cache_data(ttl=300)
def load_data():
    data = list(
        collection.find({}, {"_id": 0})
    )

    df = pd.DataFrame(data)

    if not df.empty:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"]
        )

    return df

df = load_data()

if df.empty:
    st.warning("No data available")
    st.stop()

# ---------------------------------------------------
# FILTERS
# ---------------------------------------------------
st.sidebar.header("Filters")

selected_node = st.sidebar.multiselect(
    "Select Node",
    sorted(df["node_id"].unique()),
    default=sorted(df["node_id"].unique())
)

filtered_df = df[
    df["node_id"].isin(selected_node)
]

# ---------------------------------------------------
# KPI SECTION
# ---------------------------------------------------
total_sessions = len(filtered_df)

total_users = filtered_df[
    "mac_address_hashed"
].nunique()

total_nodes = filtered_df[
    "node_id"
].nunique()

avg_duration = round(
    filtered_df[
        "connection_duration_secs"
    ].mean() / 60,
    2
)

total_data_gb = round(
    filtered_df[
        "bytes_transferred"
    ].sum() / (1024**3),
    2
)

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Sessions",
    f"{total_sessions:,}"
)

col2.metric(
    "Unique Users",
    f"{total_users:,}"
)

col3.metric(
    "Nodes",
    total_nodes
)

col4.metric(
    "Avg Duration",
    f"{avg_duration} min"
)

col5.metric(
    "Data Usage",
    f"{total_data_gb} GB"
)

st.divider()

# ---------------------------------------------------
# HOURLY CONNECTIONS
# ---------------------------------------------------
st.subheader("⏰ Hourly Connections")

filtered_df["hour"] = (
    filtered_df["timestamp"].dt.hour
)

hourly_df = (
    filtered_df
    .groupby("hour")
    .size()
    .reset_index(name="connections")
)

fig_hour = px.line(
    hourly_df,
    x="hour",
    y="connections",
    markers=True,
    title="Hourly Usage Pattern"
)

st.plotly_chart(
    fig_hour,
    use_container_width=True
)

# ---------------------------------------------------
# TOP HOTSPOTS
# ---------------------------------------------------
st.subheader("🏆 Top 10 Wi-Fi Hotspots")

top_nodes = (
    filtered_df
    .groupby("node_id")
    .size()
    .reset_index(name="sessions")
    .sort_values(
        by="sessions",
        ascending=False
    )
    .head(10)
)

fig_nodes = px.bar(
    top_nodes,
    x="node_id",
    y="sessions",
    text="sessions",
    title="Most Active Hotspots"
)

st.plotly_chart(
    fig_nodes,
    use_container_width=True
)

# ---------------------------------------------------
# DATA USAGE DISTRIBUTION
# ---------------------------------------------------
st.subheader("📡 Data Consumption")

fig_usage = px.histogram(
    filtered_df,
    x="bytes_transferred",
    nbins=40,
    title="Bytes Transferred Distribution"
)

st.plotly_chart(
    fig_usage,
    use_container_width=True
)

# ---------------------------------------------------
# SESSION DURATION
# ---------------------------------------------------
st.subheader("⌛ Session Duration Distribution")

fig_duration = px.histogram(
    filtered_df,
    x="connection_duration_secs",
    nbins=40,
    title="Connection Duration"
)

st.plotly_chart(
    fig_duration,
    use_container_width=True
)

# ---------------------------------------------------
# TOP USERS
# ---------------------------------------------------
st.subheader("👥 Most Active Users")

top_users = (
    filtered_df
    .groupby("mac_address_hashed")
    .size()
    .reset_index(name="sessions")
    .sort_values(
        by="sessions",
        ascending=False
    )
    .head(10)
)

st.dataframe(
    top_users,
    use_container_width=True
)

# ---------------------------------------------------
# NODE STATISTICS TABLE
# ---------------------------------------------------
st.subheader("📋 Node Statistics")

node_stats = (
    filtered_df
    .groupby("node_id")
    .agg(
        Sessions=("session_id", "count"),
        Users=("mac_address_hashed", "nunique"),
        Avg_Duration=("connection_duration_secs", "mean"),
        Total_Bytes=("bytes_transferred", "sum")
    )
    .reset_index()
)

st.dataframe(
    node_stats,
    use_container_width=True
)

# ---------------------------------------------------
# RAW DATA
# ---------------------------------------------------
with st.expander("View Raw Data"):
    st.dataframe(
        filtered_df,
        use_container_width=True
    )

st.markdown("---")
st.caption(
    "Public Wi-Fi Hotspot Usage Analyzer Dashboard"
)
