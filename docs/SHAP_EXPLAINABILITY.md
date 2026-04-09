# SHAP Explainability Guide - Smoothness ML Engine

## Overview

This guide explains how to use SHAP (SHapley Additive exPlanations) to understand and interpret smoothness scores.

## Quick Start

```python
from src.core.smoothness_ml_engine import ExplainableScoringEngine

# Initialize engine
engine = ExplainableScoringEngine()

# Score a trip with explanations
result = engine.score_trip_from_samples_with_explanation(trip_events)

# Get human-readable explanation
print(result['smoothness_explanation']['explanation_text'])
```

## What is SHAP?

SHAP provides a mathematically consistent way to explain predictions by:
1. **Breaking down each prediction** into contributions from each feature
2. **Assigning each feature a "contribution" value** (positive = helps score, negative = hurts score)
3. **Starting from a baseline** (model's average prediction) and adding feature contributions

### Formula

```
Prediction = Base Value + Feature1_Contribution + Feature2_Contribution + ...
```

Example:
```
87.5 = 75.0 + 8.5 + 4.0 + (-5.0)
      Base   Jerk  Accel  Brakes
```

## Output Structure

### Basic Scoring
```python
engine = ScoringEngine()
scores = engine.score_trip_from_samples(trip_events)
# Returns: {smoothness, safety, overall, sample_count, ...}
```

### Explainable Scoring
```python
engine = ExplainableScoringEngine()
result = engine.score_trip_from_samples_with_explanation(trip_events)

# Structure:
{
    "scores": {
        "smoothness": 87.5,
        "safety": 92.0,
        "overall": 89.75,
        ...
    },
    "smoothness_explanation": {
        "prediction": 87.5,
        "base_value": 75.0,
        "feature_contributions": {
            "avg_jerk": 8.5,
            "avg_accel_std": 4.0,
            "total_harsh_brakes": -5.0,
            "total_harsh_accels": -2.0
        },
        "waterfall": [
            ("base_value", 75.0),
            ("avg_jerk", 8.5),
            ("avg_accel_std", 4.0),
            ("total_harsh_brakes", -5.0),
            ("total_harsh_accels", -2.0)
        ],
        "top_positive": [
            ("avg_jerk", 8.5),
            ("avg_accel_std", 4.0)
        ],
        "top_negative": [
            ("total_harsh_brakes", -5.0),
            ("total_harsh_accels", -2.0)
        ],
        "explanation_text": "SMOOTHNESS PREDICTION: 87.5/100\n..."
    },
    "raw_features": {
        "avg_jerk": 0.008,
        "avg_accel_std": 0.10,
        "total_harsh_brakes": 2,
        "total_harsh_accels": 1,
        ...
    }
}
```

## Features Explained

### 1. **avg_jerk** (Mean Jerk)
- **What it is**: Smoothness of acceleration changes
- **Range**: 0.0 to ~0.05 (higher = choppier)
- **Good value**: < 0.01 (smooth transitions)
- **SHAP contribution**: 
  - Positive (good): Low jerk → increases smoothness
  - Negative (bad): High jerk → decreases smoothness

### 2. **avg_accel_std** (Acceleration Consistency)
- **What it is**: Variability in acceleration throughout trip
- **Range**: 0.0 to ~0.5 (higher = more jerky)
- **Good value**: < 0.15 (consistent)
- **SHAP contribution**:
  - Positive (good): Low variability → smooth driving
  - Negative (bad): High variability → inconsistent

### 3. **total_harsh_brakes** (Harsh Braking Events)
- **What it is**: Count of sudden braking (accel < -0.8 m/s²)
- **Range**: 0 to ~20 per 2-hour trip
- **Good value**: 0-2 (few harsh events)
- **SHAP contribution**:
  - Positive (good): No harsh brakes → safe
  - Negative (bad): Multiple harsh brakes → unsafe

### 4. **total_harsh_accels** (Harsh Acceleration Events)
- **What it is**: Count of sudden acceleration (accel > 0.7 m/s²)
- **Range**: 0 to ~10 per 2-hour trip
- **Good value**: 0-1 (minimal)
- **SHAP contribution**:
  - Positive (good): No harsh accels → controlled
  - Negative (bad): Multiple harsh accels → aggressive

## Interpretation Guide

### Reading SHAP Values

```
Feature: avg_jerk
Value: 0.008
Contribution: +8.5 pts

Interpretation:
Your jerk value of 0.008 is BETTER than average.
This adds +8.5 points to your smoothness score.
(Average jerk would contribute 0 pts)
```

### Positive Factors (✅)
Features that **improve** your smoothness score:
- Low jerk (smooth acceleration transitions)
- Low acceleration variability (consistent driving)
- Minimal harsh events

### Negative Factors (❌)
Features that **reduce** your smoothness score:
- High jerk (choppy acceleration)
- High acceleration variability (erratic driving)
- Multiple harsh braking/acceleration events

## Methods

### 1. explain_smoothness_prediction(trip_features)
Explains a single trip's smoothness score.

```python
features = {
    "avg_jerk": 0.008,
    "avg_accel_std": 0.10,
    "total_harsh_brakes": 2,
    "total_harsh_accels": 1
}

explanation = engine.explain_smoothness_prediction(features)
print(explanation["explanation_text"])
```

Output:
```
SMOOTHNESS PREDICTION: 87.5/100
Baseline (avg driver): 75.0/100
Your result: 87.5/100 (+12.5)

✅ POSITIVE FACTORS (improving smoothness):
  • avg_jerk: 0.008 [+8.5 pts]
  • avg_accel_std: 0.1 [+4.0 pts]

❌ NEGATIVE FACTORS (reducing smoothness):
  • total_harsh_brakes: 2 [-5.0 pts]
```

### 2. score_trip_from_samples_with_explanation(events)
Scores a trip AND explains the result.

```python
result = engine.score_trip_from_samples_with_explanation(trip_events)

print(f"Score: {result['scores']['smoothness']}/100")
print(result['smoothness_explanation']['explanation_text'])
```

### 3. get_global_feature_importance()
Shows which features matter most **fleet-wide**.

```python
importance = engine.get_global_feature_importance()
print(importance["interpretation"])
```

Output:
```
GLOBAL FEATURE IMPORTANCE (Fleet-wide)
=======================================

1. total_harsh_brakes   │████████░░░░░░░░░░░░│ 35.2%
2. avg_jerk            │██████░░░░░░░░░░░░░░│ 25.1%
3. avg_accel_std       │█████░░░░░░░░░░░░░░░│ 21.8%
4. total_harsh_accels  │████░░░░░░░░░░░░░░░░│ 17.9%
```

## Use Cases

### 1. Driver Coaching
**Goal**: Explain to a driver why their score was low

```python
engine = ExplainableScoringEngine()
result = engine.score_trip_from_samples_with_explanation(trip_events)

if result['scores']['smoothness'] < 70:
    explanation = result['smoothness_explanation']['explanation_text']
    # Send to driver: "Your smoothness was low because..."
    send_coaching_message(explanation)
```

### 2. Fleet Analytics
**Goal**: Understand what makes a good driver

```python
# Compare good vs poor drivers
good_driver_importance = engine.get_global_feature_importance()
# Shows which features differentiate good drivers
```

### 3. Quality Assurance
**Goal**: Debug scoring anomalies

```python
# Explain unexpected scores
if score < expected_score:
    explanation = engine.explain_smoothness_prediction(features)
    print("Why was this score lower than expected?")
    print(explanation['top_negative'])  # Show negative factors
```

## Examples

### Example 1: Good Driver
```
Features: low jerk (0.008), low variability (0.08), 0 harsh events

Output:
SMOOTHNESS PREDICTION: 92.0/100
Baseline: 75.0/100
Your result: 92.0/100 (+17.0)

✅ POSITIVE FACTORS:
  • avg_jerk: 0.008 [+12.0 pts]
  • avg_accel_std: 0.08 [+5.0 pts]
```

### Example 2: Poor Driver
```
Features: high jerk (0.025), high variability (0.35), 3 harsh brakes

Output:
SMOOTHNESS PREDICTION: 62.0/100
Baseline: 75.0/100
Your result: 62.0/100 (-13.0)

❌ NEGATIVE FACTORS:
  • total_harsh_brakes: 3 [-9.0 pts]
  • avg_jerk: 0.025 [-8.0 pts]
  • avg_accel_std: 0.35 [-8.5 pts]
```

## Waterfall Visualization

The `waterfall` field provides data for visualization:

```python
waterfall = explanation['waterfall']
# [
#     ("base_value", 75.0),
#     ("avg_jerk", 8.5),
#     ("avg_accel_std", 4.0),
#     ("total_harsh_brakes", -5.0),
#     ("total_harsh_accels", -2.0)
# ]

# Can be plotted as:
# |
# |         ▁▁▁
# |       / 92.0 \
# |     /    |    \
# |   /      |      \
# | 75.0  +8.5 +4.0 -5.0 -2.0
```

## Limitations & Notes

1. **SHAP requires training data**: Must train model before generating explanations
2. **Feature values matter**: Same feature name with different values has different impacts
3. **Non-linear relationships**: XGBoost captures complex interactions not obvious from individual features
4. **Baseline dependency**: SHAP values are relative to the model's baseline (average prediction)

## Advanced Usage

### Custom SHAP Analysis
```python
# Access raw SHAP values
shap_values = engine.shap_explainer.shap_values(feature_df)
base_value = engine.shap_explainer.expected_value

# Use for custom visualizations
import matplotlib.pyplot as plt
# Create custom plots combining SHAP insights
```

### Batch Explanations
```python
for trip_id, trip_events in all_trips.items():
    result = engine.score_trip_from_samples_with_explanation(trip_events)
    explanation = result['smoothness_explanation']['explanation_text']
    store_explanation(trip_id, explanation)
```

## References

- SHAP Paper: https://arxiv.org/abs/1705.07874
- SHAP GitHub: https://github.com/slundberg/shap
- XGBoost Documentation: https://xgboost.readthedocs.io/
