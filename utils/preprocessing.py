import pandas as pd
import numpy as np


# --------------------------------------------------
# CLEAN DATA
# --------------------------------------------------
def clean_data(df):
    """
    Clean Wi-Fi session dataset.
    """

    if df.empty:
        return df

    # Remove duplicates
    df = df.drop_duplicates()

    # Remove missing rows
    df = df.dropna()

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="coerce"
    )

    # Remove invalid timestamps
    df = df.dropna(
        subset=["timestamp"]
    )

    return df


# --------------------------------------------------
# FEATURE ENGINEERING
# --------------------------------------------------
def create_time_features(df):
    """
    Extract time-based features.
    """

    df["hour"] = (
        df["timestamp"].dt.hour
    )

    df["day"] = (
        df["timestamp"].dt.day
    )

    df["month"] = (
        df["timestamp"].dt.month
    )

    df["year"] = (
        df["timestamp"].dt.year
    )

    df["weekday"] = (
        df["timestamp"].dt.weekday
    )

    df["weekend"] = (
        df["weekday"]
        .isin([5, 6])
        .astype(int)
    )

    return df


# --------------------------------------------------
# DATA USAGE CATEGORY
# --------------------------------------------------
def classify_data_usage(df):
    """
    Categorize data consumption.
    """

    bins = [
        0,
        1_000_000,
        10_000_000,
        np.inf
    ]

    labels = [
        "Low",
        "Medium",
        "High"
    ]

    df["usage_category"] = pd.cut(
        df["bytes_transferred"],
        bins=bins,
        labels=labels
    )

    return df


# --------------------------------------------------
# SESSION DURATION CATEGORY
# --------------------------------------------------
def classify_duration(df):
    """
    Categorize session duration.
    """

    bins = [
        0,
        300,
        900,
        1800,
        np.inf
    ]

    labels = [
        "0-5 min",
        "5-15 min",
        "15-30 min",
        "30+ min"
    ]

    df["duration_category"] = pd.cut(
        df["connection_duration_secs"],
        bins=bins,
        labels=labels
    )

    return df


# --------------------------------------------------
# NODE ENCODING
# --------------------------------------------------
def encode_nodes(df):
    """
    Encode node IDs for ML.
    """

    df["node_encoded"] = (
        df["node_id"]
        .astype("category")
        .cat.codes
    )

    mapping = dict(
        zip(
            df["node_id"],
            df["node_encoded"]
        )
    )

    return df, mapping


# --------------------------------------------------
# CROWD DENSITY DATASET
# --------------------------------------------------
def create_density_dataset(df):
    """
    Create dataset for ML.
    """

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

    return density_df


# --------------------------------------------------
# PIPELINE
# --------------------------------------------------
def preprocess_pipeline(df):
    """
    Complete preprocessing pipeline.
    """

    df = clean_data(df)

    df = create_time_features(df)

    df = classify_data_usage(df)

    df = classify_duration(df)

    return df
