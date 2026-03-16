import sqlite3
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib

DB_NAME = "telemetry.db"
MODEL_PATH = "smoothness_model.joblib"

def generate_labels(df):
    """
    Since we don't have human-labeled data, we synthesize labels based on
    the 'strategy.md' assumptions.
    High Smoothness = Low Fluidity (Jerk), Low Consistency (StdDev), High Comfort %
    """
    # Normalize features for label synthesis
    # Fluidity: lower is better (0.05 to 0.5+)
    # Consistency: lower is better (0.1 to 1.0+)
    # Comfort: higher is better (0 to 100)
    
    # Heuristic formula for simulation:
    # smoothness = 100 - (Fluidity * 100) - (Consistency * 50) + (Comfort * 0.5)
    # We add some noise to make it realistic for ML to "learn"
    
    score = 70 - (df['accel_fluidity'] * 80) - (df['driving_consistency'] * 40) + (df['comfort_zone_percent'] * 0.4)
    # Add noise
    score += np.random.normal(0, 2, len(df))
    
    # Clip to 0-100
    return np.clip(score, 0, 100)

def train_model():
    """Trains the XGBoost model using labels generated from heuristics."""
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("""
        SELECT trip_id, accel_fluidity, driving_consistency, comfort_zone_percent 
        FROM trips 
        WHERE accel_fluidity IS NOT NULL
    """, conn)
    conn.close()

    if len(df) < 10:
        print("❌ Not enough data to train.")
        return

    # Generate labels
    df['smoothness_label'] = generate_labels(df)
    
    X = df[['accel_fluidity', 'driving_consistency', 'comfort_zone_percent']]
    y = df['smoothness_label']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"🚀 Training XGBoost on {len(X_train)} trips...")
    
    model = xgb.XGBRegressor(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        objective='reg:squarederror'
    )
    
    model.fit(X_train, y_train)

    # Evaluate
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    print(f"✅ Model Trained. MAE: {mae:.2f}, R2: {r2:.2f}")

    # Save model
    joblib.dump(model, MODEL_PATH)
    print(f"💾 Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_model()
