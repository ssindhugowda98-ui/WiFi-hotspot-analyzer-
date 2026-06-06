import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)

from mongodb.queries import get_all_sessions


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
print("Loading data from MongoDB...")

df = get_all_sessions()

if df.empty:
    raise ValueError("No data found in MongoDB")

# --------------------------------------------------
# PREPROCESSING
# --------------------------------------------------
df["timestamp"] = pd.to_datetime(df["timestamp"])

df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day
df["month"] = df["timestamp"].dt.month
df["weekday"] = df["timestamp"].dt.weekday

# --------------------------------------------------
# CREATE CROWD DENSITY DATASET
# --------------------------------------------------
density_df = (
    df.groupby(["node_id", "hour"])
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

# Save mapping
node_mapping = dict(
    zip(
        density_df["node_id"],
        density_df["node_encoded"]
    )
)

joblib.dump(
    node_mapping,
    "ml/node_mapping.pkl"
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
# TRAIN MODEL
# --------------------------------------------------
print("Training model...")

model = RandomForestRegressor(
    n_estimators=200,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)

model.fit(
    X_train,
    y_train
)

# --------------------------------------------------
# EVALUATION
# --------------------------------------------------
predictions = model.predict(X_test)

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = mean_squared_error(
    y_test,
    predictions
) ** 0.5

r2 = r2_score(
    y_test,
    predictions
)

print("\nModel Performance")
print("-" * 30)
print(f"MAE  : {mae:.2f}")
print(f"RMSE : {rmse:.2f}")
print(f"R²   : {r2:.4f}")

# --------------------------------------------------
# SAVE MODEL
# --------------------------------------------------
joblib.dump(
    model,
    "ml/crowd_density_model.pkl"
)

print("\nModel saved successfully")
print(
    "File: ml/crowd_density_model.pkl"
)
