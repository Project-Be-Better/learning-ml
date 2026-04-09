# SHAP Explainability Guide - Reward-Based Smoothness Scoring

## Overview

This guide explains how to use SHAP (SHapley Additive exPlanations) to interpret **reward-based smoothness scores** that encourage and recognize safe, smooth driving.

## Reward-Based Scoring Philosophy

The smoothness score is a **reward metric** (0-100) where:
- **50** = Normal/average driving (neutral baseline)
- **70–89** = Good driving (solid performance)
- **90+** = Excellent driving (eligible for bonuses/incentives)
- **<50** = Aggressive driving (not rewarded)

## Quick Start

```python
from src.core.smoothness_ml_engine import ExplainableScoringEngine

# Initialize engine
engine = ExplainableScoringEngine()

# Score a trip with explanations
result = engine.score_trip_from_samples_with_explanation(trip_events)

# Get human-readable explanation with behavioral insights
print(result['smoothness_explanation']['explanation_text'])
```

## What is SHAP?

SHAP provides a mathematically consistent way to explain reward predictions by:
1. **Breaking down each prediction** into contributions from each feature
2. **Assigning each feature a "reward contribution"** (positive = earns points, negative = loses opportunity)
3. **Starting from baseline 50** (normal driving) and adding feature contributions

### Formula

```
Reward Score = Base (50) + Feature1_Contribution + Feature2_Contribution + ...
```

**Example - Good Driver:**
```
78 = 50 + 8 (low jerk) + 6 (smooth acceleration) + 3 (no harsh braking) + 3 (no over-revving) + (-2 variation)
   Base  Excellent    Reward              Reward                         Reward              Minor deduction
```

**Example - Aggressive Driver:**
```
35 = 50 - 8 (high jerk) - 6 (jerky acceleration) - 5 (harsh braking) - 3 (over-revving) + margin
   Base  Lost points    Lost points              Lost opportunity     Lost points          for variation
```

## Output Structure

### Explainable Scoring with Rewards
```python
engine = ExplainableScoringEngine()
result = engine.score_trip_from_samples_with_explanation(trip_events)

# Structure:
{
    "scores": {
        "smoothness": 78,        # Reward score (0-100, baseline 50)
        "sample_count": 12,
        ...
    },
    "smoothness_explanation": {
        "prediction": 78,                    # Trip earned 78 reward points
        "base_value": 50,                    # Baseline for normal driving
        "feature_contributions": {           # What behaviors earned/lost points
            "avg_jerk": 8,                   # Earned 8 pts for low jerk
            "avg_accel_std": 6,              # Earned 6 pts for smooth acceleration
            "max_decel_g": 5,                # Earned 5 pts for gentle braking
            "total_harsh_brakes": 3,         # Earned 3 pts for no harsh brakes
            "total_harsh_accels": 3,         # Earned 3 pts for no harsh acceleration
            "total_harsh_corners": 3,        # Earned 3 pts for smooth cornering
            "avg_lateral_g": 4,              # Earned 4 pts for minimal lateral forces
            "avg_speed_std": 6,              # Earned 6 pts for consistent speed
            "avg_rpm": 5,                    # Earned 5 pts for efficient RPM
            "total_over_revs": 3,            # Earned 3 pts for no over-revving
            "total_idle_seconds": 3,         # Earned 3 pts for minimal idling
            "max_speed_kmh": 4,              # Earned 4 pts for controlled speed
            "noise": -1.8                    # Small variation (realistic)
        },
        "top_rewards": [
            ("avg_jerk", 8, "Low jerk (smooth transitions)"),
            ("avg_speed_std", 6, "Consistent speed"),
            ("avg_accel_std", 6, "Smooth acceleration pressure")
        ],
        "improvement_opportunities": [
            ("max_lateral_g", 4, "Try smoother cornering +2-3 pts"),
            ("avg_rpm", 5, "Maintain RPM < 1800 for +2 pts more")
        ],
        "explanation_text": "TRIP REWARD: 78/100\n\nBehaviors that earned points:\n✅ Low jerk (+8)\n✅ Consistent speed (+6)..."
    },
    "raw_features": {
        "avg_jerk": 0.007,
        "avg_accel_std": 0.09,
        "total_harsh_brakes": 0,
        "total_harsh_accels": 0,
        ...
    }
}
```

### 1. **avg_jerk** (Acceleration Smoothness)
- **What it is**: How smoothly driver changes acceleration
- **Reward threshold**: < 0.008 m/s³ (earns +8 pts)
- **Interpretation**: Lower is better (smoother = more reward)
- **Examples**:
  - 0.005 → Smooth, excellent transitions ✅
  - 0.010 → Jerky transitions, loses reward points

### 2. **avg_accel_std** (Consistent Acceleration Pressure)
- **What it is**: Variability in how hard driver presses pedal
- **Reward threshold**: < 0.10 g (earns +6 pts)
- **Interpretation**: Lower is better (consistent = more reward)
- **Examples**:
  - 0.08 g → Steady pressure, predictable ✅
  - 0.15 g → Erratic pressure, loses points

### 3. **total_harsh_brakes** (Abrupt Braking Events)
- **What it is**: Count of sudden hard braking moments
- **Reward threshold**: = 0 events (earns +3 pts)
- **Interpretation**: Zero is best (safety incentive)
- **Examples**:
  - 0 events → No sudden stops, full reward ✅
  - 3+ events → Reactive/emergency braking, loses opportunity

### 4. **total_harsh_accels** (Aggressive Acceleration Events)
- **What it is**: Count of sudden hard acceleration moments
- **Reward threshold**: = 0 events (earns +3 pts)
- **Interpretation**: Zero is best (fuel efficiency + safety)
- **Examples**:
  - 0 events → Smooth starts, full reward ✅
  - 2+ events → Aggressive starts, loses opportunity

### 5. **avg_lateral_g** (Smooth Cornering)
- **What it is**: Average sideways G-force during turns
- **Reward threshold**: < 0.02 g (earns +4 pts)
- **Interpretation**: Gentle cornering = more reward
- **Examples**:
  - 0.015 g → Smooth, controlled turns ✅
  - 0.05 g → Aggressive cornering, loses points

## Interpretation Guide

### Reading Reward Contributions

```
Feature: avg_jerk
Value: 0.007
Reward: +8 pts

Interpretation:
✅ Your jerk is EXCELLENT (0.007 < threshold of 0.008)
   You earned the FULL +8 reward points for smooth acceleration!
```

```
Feature: avg_jerk
Value: 0.012
Reward: 0 pts

Interpretation:
⚠️  Your jerk is above threshold (0.012 > 0.008)
   You didn't earn the +8 reward for this behavior.
   Tip: Smoother acceleration transitions would earn +8 pts.
```

### Reward Categories

#### ✅ Behaviors That Earn Points
- **Low jerk** (+8 pts) - Smooth acceleration transitions
- **Consistent acceleration** (+6 pts) - Steady pedal pressure
- **No harsh braking** (+3 pts) - Smooth, predictive braking
- **No harsh acceleration** (+3 pts) - Controlled starts
- **Smooth cornering** (+4 pts) - Gentle lateral movements
- **Consistent speed** (+6 pts) - Steady velocity, less fuel waste
- **Efficient RPM** (+5 pts) - Lower average engine speed
- **No over-revving** (+3 pts) - Controlled engine operation
- **Minimal idling** (+3 pts) - Efficient time management
- **Controlled top speed** (+4 pts) - Safety and efficiency

#### ⚠️ Behaviors That Don't Earn (Low Reward)
- High jerk - Abrupt acceleration changes
- Inconsistent acceleration - Erratic pedal control
- Harsh braking - Sudden stops
- Harsh acceleration - Aggressive starts
- Aggressive cornering - High lateral forces  
- Speed variability - Erratic velocity changes
- High RPM - Engine racing
- Over-revving - Hard on engine
- Excessive idling - Wasted fuel
- Speeding - Safety and efficiency concerns

## Methods

### 1. explain_smoothness_prediction(trip_features)
Explains a single trip's reward score.

```python
features = {
    "avg_jerk": 0.007,
    "avg_accel_std": 0.09,
    "total_harsh_brakes": 0,
    "total_harsh_accels": 0
}

explanation = engine.explain_smoothness_prediction(features)
print(explanation["explanation_text"])
```

Output:
```
🎯 TRIP REWARD SCORE: 78/100
📊 Baseline (normal driving): 50/100
📈 Your earned: 78/100 (+28 reward points)

✅ REWARDS EARNED (showing your strengths):
  • Low jerk: 0.007 [+8 pts] 🎁 Excellent smooth acceleration!
  • Consistent pressure: 0.09g [+6 pts] 🎁 Very steady driving!
  • No harsh brakes: 0 [+3 pts] 🎁 Smooth, predictive braking!
  • No harsh acceleration: 0 [+3 pts] 🎁 Controlled starts!

⚠️  IMPROVEMENT OPPORTUNITIES (next steps for more reward):
  • Speed variability: 4.2 km/h std → Target < 8.0 (+potential 6 pts)
  • RPM management: 1950 avg → Target < 2000 (+potential 5 pts)
```

### 2. score_trip_from_samples_with_explanation(events)
Scores a trip AND explains the reward breakdown.

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
