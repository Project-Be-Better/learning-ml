"""
Demonstration of SHAP-based explainability for smoothness scoring
====================================================================

This script shows how to use ExplainableScoringEngine to:
1. Score a trip from telematics samples
2. Get feature-level SHAP explanations
3. Understand what drives smoothness up or down
4. Compare drivers using global feature importance
"""

from src.core.smoothness_ml_engine import (
    ExplainableScoringEngine,
)

# Example telematics events from a device (one per 10-minute window)
GOOD_DRIVER_EVENT = {
    "trip_id": "TRIP-GOOD-001",
    "details": {
        "jerk": {"mean": 0.006, "std_dev": 0.004},  # Very low jerk = smooth
        "longitudinal": {
            "mean_accel_g": 0.02,
            "std_dev": 0.08,  # Low variability = consistent
            "harsh_brake_count": 0,
            "harsh_accel_count": 0,
        },
        "speed": {"mean_kmh": 65.0, "std_dev": 5.0, "max_kmh": 75.0},
    },
}

POOR_DRIVER_EVENT = {
    "trip_id": "TRIP-POOR-001",
    "details": {
        "jerk": {"mean": 0.025, "std_dev": 0.015},  # High jerk = choppy
        "longitudinal": {
            "mean_accel_g": 0.15,
            "std_dev": 0.35,  # High variability = jerky
            "harsh_brake_count": 3,
            "harsh_accel_count": 2,
        },
        "speed": {"mean_kmh": 82.0, "std_dev": 15.0, "max_kmh": 105.0},
    },
}


def demonstrate_good_driver():
    """Analyze a smooth driver with positive SHAP contributions."""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: GOOD DRIVER (Smooth & Safe)")
    print("=" * 80)

    trip_events = [GOOD_DRIVER_EVENT for _ in range(12)]

    engine = ExplainableScoringEngine()
    result = engine.score_trip_from_samples_with_explanation(trip_events)

    print("\n📊 TRIP SCORES:")
    print(f"  Smoothness: {result['scores']['smoothness']}/100")
    print(f"  Safety: {result['scores']['safety']}/100")
    print(f"  Overall: {result['scores']['overall']}/100")

    print("\n🔍 SHAP EXPLANATION:")
    print(result["smoothness_explanation"]["explanation_text"])

    print("\n📈 FEATURE-BY-FEATURE BREAKDOWN:")
    print(f"  Base prediction: {result['smoothness_explanation']['base_value']}/100")
    for feature, contrib in result["smoothness_explanation"][
        "feature_contributions"
    ].items():
        value = result["raw_features"].get(feature, "N/A")
        symbol = "✅" if contrib > 0 else "❌"
        print(f"  {symbol} {feature:20} = {value:8} [{contrib:+7.4f} pts]")


def demonstrate_poor_driver():
    """Analyze a rough driver with negative SHAP contributions."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: POOR DRIVER (Jerky & Unsafe)")
    print("=" * 80)

    trip_events = [POOR_DRIVER_EVENT for _ in range(12)]

    engine = ExplainableScoringEngine()
    result = engine.score_trip_from_samples_with_explanation(trip_events)

    print("\n📊 TRIP SCORES:")
    print(f"  Smoothness: {result['scores']['smoothness']}/100")
    print(f"  Safety: {result['scores']['safety']}/100")
    print(f"  Overall: {result['scores']['overall']}/100")

    print("\n🔍 SHAP EXPLANATION:")
    print(result["smoothness_explanation"]["explanation_text"])

    print("\n📈 FEATURE-BY-FEATURE BREAKDOWN:")
    print(f"  Base prediction: {result['smoothness_explanation']['base_value']}/100")
    for feature, contrib in result["smoothness_explanation"][
        "feature_contributions"
    ].items():
        value = result["raw_features"].get(feature, "N/A")
        symbol = "✅" if contrib > 0 else "❌"
        print(f"  {symbol} {feature:20} = {value:8} [{contrib:+7.4f} pts]")


def demonstrate_comparison():
    """Compare two drivers side-by-side using SHAP values."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: SIDE-BY-SIDE COMPARISON")
    print("=" * 80)

    engine = ExplainableScoringEngine()

    good_events = [GOOD_DRIVER_EVENT for _ in range(12)]
    poor_events = [POOR_DRIVER_EVENT for _ in range(12)]

    good_result = engine.score_trip_from_samples_with_explanation(good_events)
    poor_result = engine.score_trip_from_samples_with_explanation(poor_events)

    print("\n┌─────────────────────────────────────────────────────────────────┐")
    print("│ METRIC                    │ GOOD DRIVER  │ POOR DRIVER  │ DELTA   │")
    print("├─────────────────────────────────────────────────────────────────┤")

    metrics = [
        ("Smoothness Score", "smoothness"),
        ("Safety Score", "safety"),
        ("Overall Score", "overall"),
    ]

    for label, key in metrics:
        good_val = good_result["scores"][key]
        poor_val = poor_result["scores"][key]
        delta = good_val - poor_val
        print(f"│ {label:23} │ {good_val:12.1f} │ {poor_val:12.1f} │ {delta:+6.1f} │")

    print("└─────────────────────────────────────────────────────────────────┘")

    print("\nGOOD DRIVER - Most Impactful Features:")
    good_exp = good_result["smoothness_explanation"]
    for feature, contrib in good_exp["top_positive"][:3]:
        print(f"  ✅ {feature}: {contrib:+.4f}")

    print("\nPOOR DRIVER - Most Impactful Negative Factors:")
    poor_exp = poor_result["smoothness_explanation"]
    for feature, contrib in poor_exp["top_negative"][:3]:
        print(f"  ❌ {feature}: {contrib:+.4f}")


def demonstrate_global_importance():
    """Show fleet-wide feature importance using SHAP."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: GLOBAL FEATURE IMPORTANCE (Fleet-wide)")
    print("=" * 80)

    engine = ExplainableScoringEngine()
    importance = engine.get_global_feature_importance()

    if "error" not in importance:
        print("\nWhich features drive smoothness across the entire fleet?")
        print(importance["interpretation"])

        print("\nImportance Scores:")
        for feature, score in importance["feature_importance"].items():
            print(f"  • {feature}: {score:.4f}")
    else:
        print(f"Note: {importance['error']}")
        print("(This requires model training first)")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SMOOTHNESS SCORING WITH SHAP EXPLAINABILITY")
    print("=" * 80)

    try:
        demonstrate_good_driver()
    except Exception as e:
        print(f"⚠️  Good driver example failed: {e}")

    try:
        demonstrate_poor_driver()
    except Exception as e:
        print(f"⚠️  Poor driver example failed: {e}")

    try:
        demonstrate_comparison()
    except Exception as e:
        print(f"⚠️  Comparison example failed: {e}")

    try:
        demonstrate_global_importance()
    except Exception as e:
        print(f"⚠️  Global importance example failed: {e}")

    print("\n" + "=" * 80)
    print("For more details, see ExplainableScoringEngine in smoothness_ml_engine.py")
    print("=" * 80)
