---
name: behavioral_xai
description: Guidelines for maintaining the Bidirectional XAI & Fairness architecture and the Behavior Agent layer.
---

# Behavioral XAI & Fairness Skill

This skill provides the architectural blueprints and implementation standards for the **TraceData Scoring System**, specifically focusing on the intersection of Explainable AI (XAI), Fairness, and Agentic Narratives.

## 1. Core Philosophy: "Transparency over Mitigation"
We do not silently adjust scores for fairness. Instead, we provide **Bidirectional Context**:
- **XAI (Physics)**: Explains *why* a score was given based on telemetry.
- **Fairness (Context)**: Explains *how* that score compares to the driver's demographic or experience cohort.

## 2. Database Schema Standards
Always maintain the following columns in both `trips` and `drivers` tables:

| Column | Type | Purpose |
| :--- | :--- | :--- |
| `explanation_json` | TEXT/JSON | XAI data (SHAP values). |
| `fairness_metadata_json` | TEXT/JSON | Performance relative to cohort (diff, avg). |

### Migration Pattern
Use the `try_add_column` pattern in `simulator.py` to ensure schema evolution without requiring database deletions.

## 3. The Behavior Agent Narrative Pattern
The `BehaviorAgent` must synthesize JSON data into human-readable narratives using these rules:

### A. Feature Filtering
Always filter out statistical metadata that isn't a direct driver behavior:
```python
ignored_features = {"base_value"} # Intercepts are not behaviors
```

### B. Professional Coaching Tone
Use a supportive, coach-like tone that highlights performance relative to cohorts:
- **Positive**: "You are outperforming your cohort by X points..."
- **Actionable**: Focus on the top feature identified by SHAP (e.g., "Your success is driven by your excellent consistency").

## 4. XAI (SHAP) Interpretation
- **Base Value**: represents the model's "starting point."
- **Positive Impact**: Features that increased the score from the base.
- **Negative Impact**: Features that decreased the score.

## 5. Model Management & Artifacts
- **Directory**: All trained models must reside in the `models/` folder.
- **Format**: Use `.joblib` for model persistence to ensure fast loading and compatibility with Scikit-learn/XGBoost.
- **Pathing**: Use relative paths (e.g., `models/smoothness_model.joblib`) in all Python scripts to ensure portability across different environments.

## 6. Verification Workflow
1. Re-run `simulator.py` for fresh data.
2. Run `processor.py` for feature extraction.
3. Run `trainer.py` to refresh the XGBoost model.
4. Run `scoring.py` to generate XAI.
5. Run `fairness.py` to calculate cohort benchmarks.
6. Verify via `GET /driver/{id}` endpoint.
