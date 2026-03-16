import sqlite3
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

from src.core.config import DB_NAME, SMOOTHNESS_MODEL_PATH
from src.core.experiment_tracker import tracker

EXPERIMENT_NAME = "tracedata-smoothness-scoring"


def generate_labels(df):
    """
    Since we don't have human-labeled data, we synthesize labels based on
    physics-driven heuristics. High Smoothness = Low Fluidity, Low Consistency, High Comfort%.
    """
    score = 70 - (df['accel_fluidity'] * 80) - (df['driving_consistency'] * 40) + (df['comfort_zone_percent'] * 0.4)
    score += np.random.normal(0, 2, len(df))
    return np.clip(score, 0, 100)


def train_model():
    """
    Trains the XGBoost smoothness model.
    Every run is tracked in mlruns/ with:
      - Hyperparameters (n_estimators, learning_rate, max_depth)
      - Metrics (MAE, R²)
      - The model artifact (.joblib)
    """
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT trip_id, accel_fluidity, driving_consistency, comfort_zone_percent 
        FROM trips 
        WHERE accel_fluidity IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 10:
        print("❌ Not enough data to train. Run simulator.py first.")
        return None

    df['smoothness_label'] = generate_labels(df)
    X = df[['accel_fluidity', 'driving_consistency', 'comfort_zone_percent']]
    y = df['smoothness_label']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    params = {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 5,
        "objective": "reg:squarederror"
    }

    with tracker.start_run(experiment=EXPERIMENT_NAME) as run:
        # Log hyperparameters
        tracker.log_params(params)
        tracker.log_param("train_size", len(X_train))
        tracker.log_param("test_size", len(X_test))

        # Train
        print(f"🚀 Training XGBoost on {len(X_train)} trips...")
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train)

        # Evaluate
        predictions = model.predict(X_test)
        mae = mean_absolute_error(y_test, predictions)
        r2 = r2_score(y_test, predictions)

        tracker.log_metric("mae", round(mae, 4))
        tracker.log_metric("r2_score", round(r2, 4))
        print(f"✅ MAE: {mae:.2f}, R²: {r2:.4f}")

        # Quality gate
        MIN_R2 = 0.85
        if r2 < MIN_R2:
            print(f"❌ Quality gate FAILED. R²={r2:.2f} below threshold {MIN_R2}.")
            tracker.set_tag("quality_gate", "FAILED")
            return None

        tracker.set_tag("quality_gate", "PASSED")

        # Save model locally
        joblib.dump(model, SMOOTHNESS_MODEL_PATH)
        print(f"💾 Model saved to {SMOOTHNESS_MODEL_PATH}")

        # Log artifact to mlruns/
        tracker.log_artifact(str(SMOOTHNESS_MODEL_PATH), artifact_path="joblib")
        print(f"📦 Artifact logged to mlruns/{EXPERIMENT_NAME}/")

    return model


if __name__ == "__main__":
    train_model()
