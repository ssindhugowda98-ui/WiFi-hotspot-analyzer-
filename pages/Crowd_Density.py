import streamlit as st
import pandas as pd
import plotly.express as px
from pymongo import MongoClient

# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="Crowd Density Analysis",
    page_icon="👥",
    layout="wide"
)

st.title("👥 Crowd Density Analysis")
st.markdown(
    "Analyze live crowd density using unique Wi-Fi users connected to each hotspot."
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
# MONGODB AGGREGATION
# -----------------------------------------------------
@st.cache_data(ttl=300)
def load_density_data():

    pipeline = [
        {
            "$addFields": {
                "hour_window": {
                    "$dateToString": {
                        "format": "%Y-%m-%d %H:00",
                        "date": {
                            "$toDate": "$timestamp"
                        }
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "node_id": "$node_id",
                    "hour_window": "$hour_window"
                },
                "unique_users": {
                    "$addToSet": "$mac_address_hashed"
                },
                "total_sessions": {
                    "$sum": 1
                },
                "total_bytes": {
                    "$sum": "$bytes_transferred"
                }
            }
        },
        {
            "$project": {
                "_id": 0,
                "node_id": "$_id.node_id",
                "hour_window": "$_id.hour_window",
                "crowd_density": {
                    "$size": "$unique_users"
                },
                "total_sessions": 1,
                "total_bytes": 1
            }
        },
        {
            "$sort": {
                "hour_window": 1
            }
        }
    ]

    data = list(collection.aggregate(pipeline))
    return pd.DataFrame(data)

density_df = load_density_data()

if density_df.empty:
    st.warning("No crowd density data available.")
    st.stop()

# -----------------------------------------------------
# SIDEBAR FILTERS
# -----------------------------------------------------
st.sidebar.header("Filters")

selected_nodes = st.sidebar.multiselect(
    "Select Wi-Fi Nodes",
    sorted(density_df["node_id"].unique()),
    default=sorted(density_df["node_id"].unique())[:5]
)

filtered_df = density_df[
    density_df["node_id"].isin(selected_nodes)
]

# -----------------------------------------------------
# KPIs
# -----------------------------------------------------
peak_density = int(filtered_df["crowd_density"].max())

avg_density = round(
    filtered_df["crowd_density"].mean(),
    2
)

total_sessions = int(
    filtered_df["total_sessions"].sum()
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Peak Crowd Density",
    peak_density
)

col2.metric(
    "Average Density",
    avg_density
)

col3.metric(
    "Total Sessions",
    f"{total_sessions:,}"
)

st.divider()

# -----------------------------------------------------
# CROWD DENSITY OVER TIME
# -----------------------------------------------------
st.subheader("📈 Crowd Density Trend")

fig_line = px.line(
    filtered_df,
    x="hour_window",
    y="crowd_density",
    color="node_id",
    markers=True,
    title="Hourly Crowd Density"
)

fig_line.update_layout(
    xaxis_title="Hour",
    yaxis_title="Unique Users"
)

st.plotly_chart(
    fig_line,
    use_container_width=True
)

# -----------------------------------------------------
# TOP DENSE NODES
# -----------------------------------------------------
st.subheader("🔥 Top 10 Dense Hotspots")

top_nodes = (
    filtered_df
    .groupby("node_id")["crowd_density"]
    .max()
    .reset_index()
    .sort_values(
        by="crowd_density",
        ascending=False
    )
    .head(10)
)

fig_bar = px.bar(
    top_nodes,
    x="node_id",
    y="crowd_density",
    color="crowd_density",
    text="crowd_density",
    title="Most Crowded Hotspots"
)

st.plotly_chart(
    fig_bar,
    use_container_width=True
)

# -----------------------------------------------------
# HEATMAP
# -----------------------------------------------------
st.subheader("🌡 Crowd Density Heatmap")

heatmap_df = (
    filtered_df
    .pivot_table(
        values="crowd_density",
        index="node_id",
        columns="hour_window",
        aggfunc="mean"
    )
)

fig_heat = px.imshow(
    heatmap_df,
    aspect="auto",
    title="Hourly Density Heatmap"
)

st.plotly_chart(
    fig_heat,
    use_container_width=True
)

# -----------------------------------------------------
# DENSITY DISTRIBUTION
# -----------------------------------------------------
st.subheader("📊 Density Distribution")

fig_hist = px.histogram(
    filtered_df,
    x="crowd_density",
    nbins=30,
    title="Crowd Density Distribution"
)

st.plotly_chart(
    fig_hist,
    use_container_width=True
)

# -----------------------------------------------------
# SATURATED NODE ANALYSIS
# -----------------------------------------------------
st.subheader("🚨 Saturated Nodes")

NODE_CAPACITY = st.slider(
    "Assumed Node Capacity",
    50,
    500,
    100
)

saturated = filtered_df.copy()

saturated["utilization_percent"] = (
    saturated["crowd_density"]
    / NODE_CAPACITY
) * 100

top_saturated = (
    saturated
    .sort_values(
        by="utilization_percent",
        ascending=False
    )
    .head(10)
)

fig_sat = px.bar(
    top_saturated,
    x="node_id",
    y="utilization_percent",
    color="utilization_percent",
    text="utilization_percent",
    title="Top Saturated Wi-Fi Nodes"
)

st.plotly_chart(
    fig_sat,
    use_container_width=True
)

# -----------------------------------------------------
# DATA TABLE
# -----------------------------------------------------
st.subheader("📋 Crowd Density Table")

st.dataframe(
    filtered_df,
    use_container_width=True
)

# -----------------------------------------------------
# DOWNLOAD REPORT
# -----------------------------------------------------
csv = filtered_df.to_csv(index=False)

st.download_button(
    label="⬇ Download Crowd Density Report",
    data=csv,
    file_name="crowd_density_report.csv",
    mime="text/csv"
)

st.markdown("---")
st.caption(
    "Crowd Density Analysis • Public Wi-Fi Hotspot Usage Analyzer"
)
