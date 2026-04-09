# Quick Reference - SHAP Explainability

## Three Ways to Use SHAP

### 1. Basic: Get Explanation Text
```python
from src.core.smoothness_ml_engine import ExplainableScoringEngine

engine = ExplainableScoringEngine()
result = engine.score_trip_from_samples_with_explanation(trip_events)

# Human-readable explanation
print(result['smoothness_explanation']['explanation_text'])
```

**Output:**
```
SMOOTHNESS PREDICTION: 87.5/100
Baseline: 75.0/100
Your result: 87.5/100 (+12.5)

✅ POSITIVE FACTORS:
  • avg_jerk: 0.008 [+8.5 pts]
  • avg_accel_std: 0.1 [+4.0 pts]

❌ NEGATIVE FACTORS:
  • total_harsh_brakes: 2 [-5.0 pts]
```

### 2. Intermediate: Get Feature Contributions
```python
exp = result['smoothness_explanation']

# Feature-by-feature breakdown
for feature, contribution in exp['feature_contributions'].items():
    sign = "✅" if contribution > 0 else "❌"
    print(f"{sign} {feature}: {contribution:+.1f} pts")
```

### 3. Advanced: Access Raw SHAP Data
```python
exp = result['smoothness_explanation']

# Waterfall for visualization
for feature, value in exp['waterfall']:
    print(f"{feature:20s} {value:6.1f}")

# Top factors
print("Most positive:", exp['top_positive'])
print("Most negative:", exp['top_negative'])
```

## Fleet-Wide Insights
```python
engine = ExplainableScoringEngine()
importance = engine.get_global_feature_importance()

print(importance['interpretation'])
# Shows which features matter most across all drivers
```

## Feature Reference

| Feature | What It Means | Good Value | SHAP Effect |
|---------|---------------|-----------|------------|
| `avg_jerk` | Smoothness of accel changes | < 0.01 | High = Good (+) |
| `avg_accel_std` | Acceleration consistency | < 0.15 | Low = Good (+) |
| `total_harsh_brakes` | Sudden braking events | 0-2 | Low = Good (+) |
| `total_harsh_accels` | Sudden accel events | 0-1 | Low = Good (+) |
| `max_speed_observed` | Speed ceiling | < 90 km/h | Variable |

## Common Patterns

### ✅ Good Driver
- avg_jerk: 0.008 → +8 pts
- avg_accel_std: 0.08 → +4 pts
- total_harsh_brakes: 0 → 0 pts
- **Result: 87-92/100**

### ❌ Poor Driver
- avg_jerk: 0.025 → -8 pts
- avg_accel_std: 0.35 → -8 pts
- total_harsh_brakes: 3 → -9 pts
- **Result: 60-65/100**

## Integration Points

### API Endpoint
```python
@app.get("/trips/{trip_id}/explanation")
def explain_trip(trip_id: str):
    engine = ExplainableScoringEngine()
    result = engine.score_trip_from_samples_with_explanation(events)
    return result['smoothness_explanation']
```

### Driver Coaching
```python
if score < 70:
    # Use explanation to coach driver
    explanation = result['smoothness_explanation']['explanation_text']
    send_message_to_driver(explanation)
```

### Analytics Dashboard
```python
importance = engine.get_global_feature_importance()
# importance['importance_dict'] has feature weights
# importance['feature_names'] has sorted names
# Use for fleet-wide insights
```

## SHAP Interpretation Rules

| Contribution | Meaning |
|------------|---------|
| +8.5 | Feature helps smoothness (better than average) |
| -5.0 | Feature hurts smoothness (worse than average) |
| 0.0 | Feature is average (no impact) |

The sum of all contributions = Prediction - Base Value

Example:
```
Base: 75.0
+8.5 (jerk) + 4.0 (accel) - 5.0 (brakes) = 7.5 total delta
Prediction: 75.0 + 7.5 = 82.5
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "No training data exists" | Model not trained | Run `python -m src.core.smoothness_ml_engine` |
| All SHAP values are 0 | Model just trained/untrained | Verify R² ≥ 0.85 quality gate passed |
| Missing features | Parse error | Check telematics event format |

## Running Examples

```bash
# See 4 demo scenarios
python demo_shap_explainability.py

# Train model and test SHAP
python -m src.core.smoothness_ml_engine
```

## Files to Know

- **Engine**: `src/core/smoothness_ml_engine.py` - Core implementation
- **Demo**: `demo_shap_explainability.py` - 4 usage examples
- **Guide**: `docs/SHAP_EXPLAINABILITY.md` - Full documentation
- **Reference**: `docs/SHAP_QUICK_REFERENCE.md` - This file
