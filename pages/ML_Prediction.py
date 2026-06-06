import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from pymongo import MongoClient

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="ML Prediction",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Crowd Density Prediction")
st.markdown(
    """
    Predict future Wi-Fi hotspot crowd density
    using Machine Learning.
    """
)

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------
@st.cache_resource
def get_db():

    client = MongoClient(
        st.secrets["MONGO_URI"]
    )

    return client["wifi_db"]

db = get_db()

collection = db["wifi_sessions"]

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
@st.cache_data(ttl=300)
def load_data():

    data = list(
        collection.find(
            {},
            {"_id": 0}
        )
    )

    df = pd.DataFrame(data)

    return df

df = load_data()

if df.empty:
    st.warning("No data found")
    st.stop()

# --------------------------------------------------
# DATA PREPROCESSING
# --------------------------------------------------
df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

df["hour"] = (
    df["timestamp"].dt.hour
)

df["day"] = (
    df["timestamp"].dt.day
)

df["month"] = (
    df["timestamp"].dt.month
)

# --------------------------------------------------
# CREATE TARGET
# Crowd Density per Node-Hour
# --------------------------------------------------
density_df = (
    df.groupby(
        [
            "node_id",
            "hour"
        ]
    )
    .agg(
        crowd_density=(
            "mac_address_hashed",
            "nunique"
        ),
        avg_duration=(
            "connection_duration_secs",
            "mean"
        ),
        total_bytes=(
            "bytes_transferred",
            "sum"
        )
    )
    .reset_index()
)

# --------------------------------------------------
# ENCODE NODE ID
# --------------------------------------------------
density_df["node_encoded"] = (
    density_df["node_id"]
    .astype("category")
    .cat.codes
)

# --------------------------------------------------
# FEATURES
# --------------------------------------------------
X = density_df[
    [
        "node_encoded",
        "hour",
        "avg_duration",
        "total_bytes"
    ]
]

y = density_df["crowd_density"]

# --------------------------------------------------
# TRAIN TEST SPLIT
# --------------------------------------------------
X_train, X_test, y_train, y_test = (
    train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )
)

# --------------------------------------------------
# MODEL
# --------------------------------------------------
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(
    X_train,
    y_train
)

# --------------------------------------------------
# PREDICTIONS
# --------------------------------------------------
predictions = model.predict(
    X_test
)

# --------------------------------------------------
# METRICS
# --------------------------------------------------
mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)

r2 = r2_score(
    y_test,
    predictions
)

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------
col1, col2, col3 = st.columns(3)

col1.metric(
    "MAE",
    round(mae, 2)
)

col2.metric(
    "RMSE",
    round(rmse, 2)
)

col3.metric(
    "R² Score",
    round(r2, 3)
)

st.divider()

# --------------------------------------------------
# ACTUAL VS PREDICTED
# --------------------------------------------------
results = pd.DataFrame(
    {
        "Actual": y_test,
        "Predicted": predictions
    }
)

st.subheader(
    "📈 Actual vs Predicted Crowd Density"
)

fig = px.scatter(
    results,
    x="Actual",
    y="Predicted",
    title="Prediction Accuracy"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# --------------------------------------------------
# FEATURE IMPORTANCE
# --------------------------------------------------
st.subheader(
    "🎯 Feature Importance"
)

importance_df = pd.DataFrame(
    {
        "Feature": X.columns,
        "Importance":
        model.feature_importances_
    }
)

importance_df = (
    importance_df
    .sort_values(
        by="Importance",
        ascending=False
    )
)

fig_imp = px.bar(
    importance_df,
    x="Feature",
    y="Importance",
    text="Importance",
    title="Feature Importance"
)

st.plotly_chart(
    fig_imp,
    use_container_width=True
)

# --------------------------------------------------
# USER PREDICTION
# --------------------------------------------------
st.subheader(
    "🔮 Predict Future Crowd Density"
)

node_options = sorted(
    density_df["node_id"].unique()
)

selected_node = st.selectbox(
    "Node ID",
    node_options
)

selected_hour = st.slider(
    "Hour",
    0,
    23,
    12
)

avg_duration = st.number_input(
    "Average Duration (secs)",
    60,
    10000,
    1800
)

total_bytes = st.number_input(
    "Total Bytes",
    1000,
    50000000,
    500000
)

# Node Encoding
node_code = (
    density_df[
        density_df["node_id"]
        == selected_node
    ]["node_encoded"]
    .iloc[0]
)

prediction_input = pd.DataFrame(
    {
        "node_encoded":
        [node_code],

        "hour":
        [selected_hour],

        "avg_duration":
        [avg_duration],

        "total_bytes":
        [total_bytes]
    }
)

predicted_density = (
    model.predict(
        prediction_input
    )[0]
)

st.success(
    f"Predicted Crowd Density: "
    f"{round(predicted_density)} Users"
)

# --------------------------------------------------
# DOWNLOAD PREDICTIONS
# --------------------------------------------------
results_csv = (
    results.to_csv(
        index=False
    )
)

st.download_button(
    label="⬇ Download Predictions",
    data=results_csv,
    file_name="predictions.csv",
    mime="text/csv"
)

# --------------------------------------------------
# MODEL INFORMATION
# --------------------------------------------------
with st.expander(
    "Model Details"
):
    st.write(
        """
        Algorithm:
        Random Forest Regressor

        Features:
        - Node ID
        - Hour
        - Average Duration
        - Total Bytes

        Target:
        - Crowd Density
        """
    )

st.markdown("---")

st.caption(
    "Machine Learning Prediction • Public Wi-Fi Hotspot Usage Analyzer"
)
