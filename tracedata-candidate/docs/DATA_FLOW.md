# Data Flow with Comprehensive Feature Architecture

## Device → Engine → Score

```
╔════════════════════════════════════════════════════════════════════════╗
║                   TELEMATICS DEVICE (Every 10 mins)                    ║
║                                                                         ║
║  Raw Sensor Data:                                                       ║
║  • Accelerometer (2-axis)      • Engine sensors (RPM)                  ║
║  • Gyroscope (lateral motion)  • Speed (GPS)                           ║
║  • Brake pressure              • GPS location                          ║
╚════════════════════════════════════════════════════════════════════════╝
                                   ↓
┌─ DEVICE AGGREGATES DATA INTO SMOOTHNESS_LOG EVENT ─────────────────────┐
│                                                                          │
│ Window: 600 seconds (10 minutes)                                        │
│ Sample Count: 600 (1 per second)                                        │
│                                                                          │
│ OUTPUT STRUCTURE:                                                        │
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │ event.details {                                                  │   │
│ │   ┌ LONGITUDINAL (Acceleration/Braking) ──────────────┐         │   │
│ │   │ • mean_accel_g: 0.04                             │         │   │
│ │   │ • std_dev: 0.12                                  │         │   │
│ │   │ • max_decel_g: -0.31                             │         │   │
│ │   │ • harsh_brake_count: 0                           │         │   │
│ │   │ • harsh_accel_count: 0                           │         │   │
│ │   └──────────────────────────────────────────────────┘         │   │
│ │                                                                  │   │
│ │   ┌ LATERAL (Cornering/Turning) ────────────────────┐         │   │
│ │   │ • mean_lateral_g: 0.02                          │         │   │
│ │   │ • max_lateral_g: 0.18                           │         │   │
│ │   │ • harsh_corner_count: 0                         │         │   │
│ │   └──────────────────────────────────────────────────┘         │   │
│ │                                                                  │   │
│ │   ┌ SPEED (Velocity Consistency) ────────────────────┐         │   │
│ │   │ • mean_kmh: 72.3                                │         │   │
│ │   │ • std_dev: 8.1                                  │         │   │
│ │   │ • max_kmh: 94.0                                 │         │   │
│ │   │ • variance: 65.61                               │         │   │
│ │   └──────────────────────────────────────────────────┘         │   │
│ │                                                                  │   │
│ │   ┌ JERK (Acceleration Smoothness) ─────────────────┐         │   │
│ │   │ • mean: 0.008                                   │         │   │
│ │   │ • max: 0.041                                    │         │   │
│ │   │ • std_dev: 0.006                                │         │   │
│ │   └──────────────────────────────────────────────────┘         │   │
│ │                                                                  │   │
│ │   ┌ ENGINE (RPM Management) ──────────────────────────┐        │   │
│ │   │ • mean_rpm: 1820                                │        │   │
│ │   │ • max_rpm: 2340                                 │        │   │
│ │   │ • idle_seconds: 45                              │        │   │
│ │   │ • idle_events: 1                                │        │   │
│ │   │ • over_rev_count: 0                             │        │   │
│ │   │ • over_rev_seconds: 0                           │        │   │
│ │   └──────────────────────────────────────────────────┘        │   │
│ │ }                                                               │   │
│ └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│ TOTAL: 18 FEATURES PER WINDOW                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                   ↓
╔════════════════════════════════════════════════════════════════════════╗
║                       ENGINE: parse_telematics_event()                  ║
║                                                                         ║
║  Input: Single 10-minute event                                         ║
║  ▼ Parses all 18 fields from event.details                        ║
║  Output: Dict with 18 parsed features                                  ║
║                                                                         ║
║  Returns:                                                               ║
║  {                                                                      ║
║    # Longitudinal (5)                                                   ║
║    "mean_accel_g": 0.04,                                               ║
║    "accel_std_g": 0.12,                                                ║
║    "max_decel_g": 0.31,                                                ║
║    "harsh_brake_count": 0,                                             ║
║    "harsh_accel_count": 0,                                             ║
║    # Lateral (3)                                                        ║
║    "mean_lateral_g": 0.02,                                             ║
║    "max_lateral_g": 0.18,                                              ║
║    "harsh_corner_count": 0,                                            ║
║    # Speed (3)                                                          ║
║    "mean_speed_kmh": 72.3,                                             ║
║    "speed_std": 8.1,                                                   ║
║    "max_speed_kmh": 94.0,                                              ║
║    # Jerk (3)                                                           ║
║    "jerk_mean": 0.008,                                                 ║
║    "jerk_std": 0.006,                                                  ║
║    "jerk_max": 0.041,                                                  ║
║    # Engine (4)                                                         ║
║    "mean_rpm": 1820,                                                   ║
║    "max_rpm": 2340,                                                    ║
║    "idle_seconds": 45,                                                 ║
║    "over_rev_count": 0,                                                ║
║  }                                                                      ║
╚════════════════════════════════════════════════════════════════════════╝
                                   ↓
               ┌─── For 2-hour trip: Repeat 12 times ───┐
               │  (1 event every 10 minutes)            │
               │                                        │
               │  Sample 1:  0-10 min    ✓             │
               │  Sample 2:  10-20 min   ✓             │
               │  Sample 3:  20-30 min   ✓             │
               │  ...                                   │
               │  Sample 12: 110-120 min ✓             │
               └────────────────────────────────────────┘
                                   ↓
╔════════════════════════════════════════════════════════════════════════╗
║                    ENGINE: aggregate_trip_samples()                     ║
║                                                                         ║
║  Input: List of 12 telematics events                                   ║
║  ▼ Aggregates across all samples                                  ║
║  Output: Trip-level features                                           ║
║                                                                         ║
║  AGGREGATION STRATEGY:                                                 ║
║                                                                         ║
║  Means (average):                                                       ║
║    - avg_accel_g      = mean(0.04, 0.035, 0.038, ...)               ║
║    - avg_accel_std    = mean(0.12, 0.14, 0.11, ...)                ║
║    - avg_lateral_g    = mean(0.02, 0.018, 0.022, ...)              ║
║    - avg_speed_kmh    = mean(72.3, 71.8, 73.1, ...)                ║
║    - avg_speed_std    = mean(8.1, 7.9, 8.3, ...)                   ║
║    - avg_jerk         = mean(0.008, 0.009, 0.007, ...)              ║
║    - avg_jerk_std     = mean(0.006, 0.007, 0.005, ...)              ║
║    - avg_rpm          = mean(1820, 1850, 1800, ...)                 ║
║                                                                         ║
║  Maxima (peak values):                                                 ║
║    - max_decel_g      = max(0.31, 0.28, 0.35, ...)                  ║
║    - max_lateral_g    = max(0.18, 0.22, 0.16, ...)                  ║
║    - max_speed_kmh    = max(94.0, 92.5, 96.2, ...)                  ║
║    - max_jerk         = max(0.041, 0.038, 0.045, ...)               ║
║    - max_rpm          = max(2340, 2280, 2420, ...)                  ║
║                                                                         ║
║  Sums (total counts/time):                                             ║
║    - total_harsh_brakes   = 0 + 1 + 0 + ... = 2 events              ║
║    - total_harsh_accels   = 0 + 1 + 0 + ... = 1 event               ║
║    - total_harsh_corners  = 0 + 0 + 1 + ... = 1 event               ║
║    - total_over_revs      = 0 + 0 + 1 + ... = 1 event               ║
║    - total_idle_seconds   = 45 + 38 + 42 + ... = 480 sec            ║
║                                                                         ║
║  Returns:                                                               ║
║  {                                                                      ║
║    "avg_accel_g": 0.038,        # Longitudinal (5)                    ║
║    "avg_accel_std": 0.121,                                             ║
║    "max_decel_g": 0.352,                                               ║
║    "total_harsh_brakes": 2,                                            ║
║    "total_harsh_accels": 1,                                            ║
║                                                                         ║
║    "avg_lateral_g": 0.019,      # Lateral (3)                         ║
║    "max_lateral_g": 0.188,                                             ║
║    "total_harsh_corners": 1,                                           ║
║                                                                         ║
║    "avg_speed_kmh": 72.4,       # Speed (3)                           ║
║    "avg_speed_std": 8.13,                                              ║
║    "max_speed_kmh": 94.8,                                              ║
║                                                                         ║
║    "avg_jerk": 0.0083,          # Jerk (3)                            ║
║    "avg_jerk_std": 0.0062,                                             ║
║    "max_jerk": 0.042,                                                  ║
║                                                                         ║
║    "avg_rpm": 1823,             # Engine (4)                           ║
║    "max_rpm": 2380,                                                    ║
║    "total_idle_seconds": 480,                                          ║
║    "total_over_revs": 1,                                               ║
║                                                                         ║
║    "sample_count": 12,          # Metadata                             ║
║  }                                                                      ║
╚════════════════════════════════════════════════════════════════════════╝
                                   ↓
╔════════════════════════════════════════════════════════════════════════╗
║                 ENGINE: XGBoost Model Prediction                        ║
║                                                                         ║
║  Input: 18 aggregated trip features (as DataFrame)                     ║
║  Model: Trained XGBoost regressor (150 trees, depth=6)                ║
║  ▼ Predicts smoothness score using all 18 inputs                  ║
║  Output: smoothness_score (0-100)                                      ║
║                                                                         ║
║  ┌──────────────────────────────────────────────────────────────┐     ║
║  │ Prediction Process:                                          │     ║
║  │                                                              │     ║
║  │  Feature Input Layer:                                        │     ║
║  │  ┌────────────────┬────────────────────────────────────┐    │     ║
║  │  │ avg_accel_g    │ 0.038 ───┐                        │    │     ║
║  │  │ avg_accel_std  │ 0.121    │                        │    │     ║
║  │  │ max_decel_g    │ 0.352    │                        │    │     ║
║  │  │ harsh_brakes   │ 2        ├──→ XGBoost Ensemble    │    │     ║
║  │  │ harsh_accels   │ 1        │    (150 decision       │    │     ║
║  │  │ ... (13 more)  │ ...      │     trees)             │    │     ║
║  │  │                │          │                        │    │     ║
║  │  │ total_over_revs│ 1     ───┘                        │    │     ║
║  │  └────────────────┴────────────────────────────────────┘    │     ║
║  │                                                              │     ║
║  │  → Each tree votes on smoothness score                      │     ║
║  │  → Average of all trees = Final prediction                  │     ║
║  │                                                              │     ║
║  │  Output: 81.7 (smoothness score)                            │     ║
║  └──────────────────────────────────────────────────────────────┘     ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
                                   ↓
╔════════════════════════════════════════════════════════════════════════╗
║                     ENGINE: score_trip_from_samples()                   ║
║                                                                         ║
║  Input: Original 12 telematics events                                  ║
║  ▼ Scores trip using all components                            ║
║  Output: Complete scoring result                                       ║
║                                                                         ║
║  Calculations:                                                          ║
║  1. Aggregate features (18 trip-level features)                        ║
║  2. XGBoost prediction → smoothness_score (81.7)                       ║
║  3. Safety score formula → safety_score (85.0)                         ║
║     = 100 - (harsh_brakes × 3) - (harsh_accels × 2)                   ║
║     = 100 - (2×3) - (1×2) = 100 - 8 = 92.0                           ║
║     Wait, includes harsh_corners & over_revs:                          ║
║     = 100 - 6 - 2 - 6 - 1 = 85.0                                      ║
║  4. Overall = (81.7 + 85.0) / 2 = 83.35                               ║
║                                                                         ║
║  Returns:                                                               ║
║  {                                                                      ║
║    "smoothness": 81.7,          # XGBoost prediction                   ║
║    "safety": 85.0,              # Rule-based calculation               ║
║    "overall": 83.35,            # Average of both                      ║
║    "sample_count": 12,                                                 ║
║    "harsh_brakes": 2,                                                  ║
║    "harsh_accels": 1,                                                  ║
║    "harsh_corners": 1,          # NEW                                  ║
║    "max_speed_kmh": 94.8,                                              ║
║    "avg_speed_kmh": 72.4,                                              ║
║    "max_rpm": 2380,             # NEW                                  ║
║    "over_revs": 1,              # NEW                                  ║
║    "idle_seconds": 480,         # NEW                                  ║
║    "raw_features": {            # NEW - full 18-feature dict           ║
║      "avg_accel_g": ...,                                               ║
║      ... (all 18 features)                                             ║
║    }                                                                    ║
║  }                                                                      ║
╚════════════════════════════════════════════════════════════════════════╝
                                   ↓
╔════════════════════════════════════════════════════════════════════════╗
║               ExplainableScoringEngine: SHAP Analysis                   ║
║                                                                         ║
║  Input: 18 trip features                                               ║
║  ▼ Explains each feature's contribution to prediction            ║
║  Output: Detailed breakdown + visualization data                       ║
║                                                                         ║
║  Configuration:                                                         ║
║  • SHAP TreeExplainer (initialized on training data)                   ║
║  • Uses XGBoost model's internal tree structure                        ║
║  • Computes Shapley values for each feature                            ║
║                                                                         ║
║  For our trip (smoothness = 81.7):                                     ║
║                                                                         ║
║  Base Value (average across training data): 78.0                       ║
║                                                                         ║
║  Feature Contributions:                                                 ║
║    avg_accel_g:      +0.5 (slightly better than average)              ║
║    avg_accel_std:    -1.2 (slightly worse)                            ║
║    max_decel_g:      -2.1 (moderate penalty)                          ║
║    harsh_brakes:     -6.0 (2 events = bad)                            ║
║    harsh_accels:     -3.5 (1 event = moderate)                        ║
║    avg_lateral_g:    +1.1 (good cornering)                            ║
║    max_lateral_g:    -2.0 (some hard turns)                           ║
║    harsh_corners:    -0.8 (minimal issue)                             ║
║    avg_speed_kmh:    -0.3 (slightly high)                             ║
║    avg_speed_std:    -4.2 (speed variance issue)                      ║
║    avg_jerk:         -2.0 (some jerkiness)                            ║
║    (other features): ±small                                            ║
║  ────────────────────────────────────────────────                      ║
║  Waterfall: 78.0 + (0.5-1.2-2.1-6.0-3.5...) = 81.7 ✓                 ║
║                                                                         ║
║  Output (SHAP explanation format):                                     ║
║  {                                                                      ║
║    "prediction": 81.7,          # Final score                          ║
║    "base_value": 78.0,          # Average model output                 ║
║    "feature_contributions": {   # Dict of feature: SHAP_value          ║
║      "avg_accel_g": 0.5,                                               ║
║      "harsh_brakes": -6.0,                                             ║
║      ...                                                               ║
║    },                                                                   ║
║    "waterfall": [               # Ordered for visualization            ║
║      ("base_value", 78.0),                                             ║
║      ("harsh_brakes", -6.0),                                           ║
║      ("avg_speed_std", -4.2),                                          ║
║      ...                                                               ║
║    ],                                                                   ║
║    "top_positive": [            # Features helping score               ║
║      ("avg_lateral_g", 1.1),                                           ║
║      ("avg_accel_g", 0.5),                                             ║
║    ],                                                                   ║
║    "top_negative": [            # Features hurting score               ║
║      ("harsh_brakes", -6.0),                                           ║
║      ("avg_speed_std", -4.2),                                          ║
║      ("harsh_accels", -3.5),                                           ║
║    ],                                                                   ║
║    "explanation_text":          # Human-readable                       ║
║      "SMOOTHNESS: 81.7/100\\n                                          ║
║       Baseline: 78.0/100\\n                                            ║
║       ✅ avg_lateral_g: +1.1 pts (smooth cornering)\\n                 ║
║       ❌ harsh_brakes: -6.0 pts (2 harsh events)\\n                    ║
║       ..."                                                              ║
║  }                                                                      ║
║                                                                         ║
╚════════════════════════════════════════════════════════════════════════╝
```

## Summary

```
Single Raw Event (10-min window)
        ↓ parse_telematics_event()
    18 Parsed Features
        ↓ × 12 (collect for 2-hour trip)
    12 Sample Events
        ↓ aggregate_trip_samples()
    1 Trip Feature Set (18 aggregates)
        ↓ predict_smoothness_score()
    Smoothness Score (XGBoost)
        + calculate_safety_score()
    Safety Score (Rule-based)
        = Final Trip Score
        + SHAP Analysis
    Score Explanation (interpretable)
```

## Feature Importance for Model

Top contributing features (in typical usage):
1. `total_harsh_brakes` (35%)
2. `avg_accel_std` (20%)
3. `avg_jerk` (18%)
4. `max_lateral_g` (12%)
5. Other features (15%)

Total: 100% of model explanation

---

**Data Collection Location**: Device sends smoothness_log every 10 minutes
**Processing Location**: Engine aggregates on demand (not real-time)
**Storage**: Aggregated features stored in trips table (DB)
**Retrieval**: Used for scoring and model training
