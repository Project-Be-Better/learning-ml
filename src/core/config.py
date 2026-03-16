import os

# --- PROJECT PATHS ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(PROJECT_ROOT, "telemetry.db")
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "smoothness_model.joblib")

# --- DATABASE CONFIG ---
DB_NAME = DB_PATH # For sqlite3.connect()

# --- MODEL CONFIG ---
SMOOTHNESS_MODEL_PATH = MODEL_PATH
