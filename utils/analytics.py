import pandas as pd


# --------------------------------------------------
# OVERALL KPI METRICS
# --------------------------------------------------
def get_kpis(df):
    """
    Calculate dashboard KPIs.
    """

    metrics = {
        "total_sessions": len(df),

        "unique_users":
        df["mac_address_hashed"].nunique(),

        "total_nodes":
        df["node_id"].nunique(),

        "avg_duration":
        round(
            df[
                "connection_duration_secs"
            ].mean() / 60,
            2
        ),

        "total_data_gb":
        round(
            df[
                "bytes_transferred"
            ].sum() / (1024**3),
            2
        )
    }

    return metrics


# --------------------------------------------------
# TOP HOTSPOTS
# --------------------------------------------------
def get_top_hotspots(
    df,
    top_n=10
):
    """
    Most utilized Wi-Fi nodes.
    """

    return (
        df.groupby("node_id")
        .size()
        .reset_index(
            name="sessions"
        )
        .sort_values(
            by="sessions",
            ascending=False
        )
        .head(top_n)
    )


# --------------------------------------------------
# PEAK HOURS
# --------------------------------------------------
def get_peak_hours(df):
    """
    Connection count by hour.
    """

    hourly = (
        df.groupby("hour")
        .size()
        .reset_index(
            name="connections"
        )
    )

    return hourly


# --------------------------------------------------
# CROWD DENSITY
# --------------------------------------------------
def get_crowd_density(df):
    """
    Unique users per hotspot.
    """

    density = (
        df.groupby("node_id")
        .agg(
            crowd_density=(
                "mac_address_hashed",
                "nunique"
            )
        )
        .reset_index()
        .sort_values(
            by="crowd_density",
            ascending=False
        )
    )

    return density


# --------------------------------------------------
# NODE STATISTICS
# --------------------------------------------------
def get_node_statistics(df):
    """
    Detailed hotspot statistics.
    """

    stats = (
        df.groupby("node_id")
        .agg(
            sessions=(
                "session_id",
                "count"
            ),

            users=(
                "mac_address_hashed",
                "nunique"
            ),

            total_bytes=(
                "bytes_transferred",
                "sum"
            ),

            avg_duration=(
                "connection_duration_secs",
                "mean"
            )
        )
        .reset_index()
    )

    return stats


# --------------------------------------------------
# SATURATION ANALYSIS
# --------------------------------------------------
def get_saturated_nodes(
    df,
    node_capacity=100
):
    """
    Calculate utilization percentage.
    """

    density = (
        df.groupby("node_id")
        .agg(
            users=(
                "mac_address_hashed",
                "nunique"
            )
        )
        .reset_index()
    )

    density[
        "utilization_percent"
    ] = (
        density["users"]
        / node_capacity
    ) * 100

    return (
        density
        .sort_values(
            by="utilization_percent",
            ascending=False
        )
    )


# --------------------------------------------------
# DATA USAGE ANALYSIS
# --------------------------------------------------
def get_data_usage_summary(df):
    """
    Analyze network traffic.
    """

    summary = {
        "total_gb":
        round(
            df[
                "bytes_transferred"
            ].sum() / (1024**3),
            2
        ),

        "avg_mb":
        round(
            df[
                "bytes_transferred"
            ].mean() / (1024**2),
            2
        ),

        "max_mb":
        round(
            df[
                "bytes_transferred"
            ].max() / (1024**2),
            2
        )
    }

    return summary


# --------------------------------------------------
# SESSION DURATION ANALYSIS
# --------------------------------------------------
def get_duration_summary(df):
    """
    Duration statistics.
    """

    return {
        "avg_minutes":
        round(
            df[
                "connection_duration_secs"
            ].mean() / 60,
            2
        ),

        "max_minutes":
        round(
            df[
                "connection_duration_secs"
            ].max() / 60,
            2
        ),

        "min_minutes":
        round(
            df[
                "connection_duration_secs"
            ].min() / 60,
            2
        )
    }


# --------------------------------------------------
# LOCATION ANALYSIS
# --------------------------------------------------
def get_location_density(df):
    """
    Density by coordinates.
    """

    location_df = (
        df.groupby(
            [
                "coordinates_lat",
                "coordinates_lon"
            ]
        )
        .agg(
            sessions=(
                "session_id",
                "count"
            ),

            users=(
                "mac_address_hashed",
                "nunique"
            )
        )
        .reset_index()
    )

    return location_df


# --------------------------------------------------
# ANOMALY DETECTION RULE
# --------------------------------------------------
def detect_high_usage_nodes(
    df,
    threshold=95
):
    """
    Find overloaded nodes.
    """

    density = get_saturated_nodes(
        df,
        node_capacity=100
    )

    anomalies = density[
        density[
            "utilization_percent"
        ] > threshold
    ]

    return anomalies


# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------
def get_dashboard_summary(df):
    """
    Complete dashboard summary.
    """

    return {
        "kpis":
        get_kpis(df),

        "top_hotspots":
        get_top_hotspots(df),

        "peak_hours":
        get_peak_hours(df),

        "crowd_density":
        get_crowd_density(df),

        "node_stats":
        get_node_statistics(df)
    }
