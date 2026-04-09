# Quick Reference Guide - Reward-Based Smoothness Scoring

**For when you're in a hurry and need to remember something quickly**

---

## 🎯 Score Quick Lookup

**What does my score mean?**

| Score | Meaning | Example Driver |
|-------|---------|---|
| **90+** | Excellent - Eligible for bonuses | Smooth, consistent, safe |
| **70–89** | Good - Solid, rewarded performance | Generally smooth, few issues |
| **50–69** | Average - Normal operation | Variable, occasional rough moments |
| **<50** | Poor - Not rewarded | Aggressive, jerky, unsafe |

**How are points earned?** (from baseline of 50)
- Smooth acceleration +8
- Consistent pressure +6
- Gentle braking +5
- No harsh braking +3
- No harsh acceleration +3
- Smooth cornering +4
- Consistent speed +6  
- Efficient RPM +5
- No over-revving +3
- Minimal idling +3
- Controlled top speed +4

---

## ⚡ Command Cheatsheet

### Setup (One Time)
```bash
# Navigate to project
cd tracedata-candidate

# Install packages
pip install mlflow xgboost scikit-learn pandas numpy
```

### Run Training
```bash
# Option 1: Direct Python (from root)
python -m src.mlops.training_pipeline

# Option 2: Windows batch script
run_mlops_training.bat

# Option 3: Linux/Mac bash script
bash run_mlops_training.sh
```

### View Results
```bash
# Start MLFlow web interface
mlflow ui

# Then open: http://localhost:5000
# View: Experiments → smoothness-scoring-production
```

---

## 📊 Key Metrics to Watch

| Metric | What It Means | Target |
|--------|---|---|
| **Test R²** | How well model predicts scores | ≥ 0.85 |
| **Test RMSE** | Average prediction error | < 5 pts |
| **CV Mean R²** | Consistency across splits | ≥ 0.85 |
| **MAE** | Mean absolute error | < 3 pts |

---

## 🎯 What Should I Read?

| What I Want | Read This | Why |
|-----------|-----------|-----|
| Just get it working | GETTING_STARTED.md | Step-by-step instructions |
| Understand the system | docs/ARCHITECTURE.md | How all pieces fit together |
| Know what earns rewards | docs/FEATURE_ENGINEERING.md | 12 reward behaviors explained |
| See data flow visually | docs/DATA_FLOW.md | ASCII diagrams |
| Train and tune | docs/MLOPS_GUIDE.md | Complete training guide |
| Understand predictions | docs/SHAP_EXPLAINABILITY.md | Why trips earn their score |
| Read the code | src/core/smoothness_ml_engine.py | Generate labels logic |

---

## 📂 File Structure Reminder

```
tracedata-candidate/
├── README.md                          ← Start here
├── GETTING_STARTED.md                 ← Step-by-step tutorial
├── src/                               ← All code
│   ├── core/smoothness_ml_engine.py   ← Main ML logic
│   ├── utils/data_generation_strategy.py ← Create fake data
│   └── mlops/training_pipeline.py     ← Train model
├── docs/                              ← Documentation
│   ├── ARCHITECTURE.md                ← Big picture
│   ├── FEATURE_ENGINEERING.md         ← 18 features explained
│   ├── DATA_FLOW.md                   ← Visualizations
│   ├── MLOPS_GUIDE.md                 ← Training guide
│   ├── SHAP_EXPLAINABILITY.md         ← Understanding results
│   └── SHAP_QUICK_REFERENCE.md        ← Quick lookup
├── config/                            ← Settings
│   └── mlops_config.yaml              ← Edit to tune
├── scripts/                           ← Automation
│   ├── run_mlops_training.bat         ← Windows
│   └── run_mlops_training.sh          ← Linux/Mac
└── (Generated after training)
    ├── data/                          ← Training data
    ├── models/                        ← Trained model
    ├── mlruns/                        ← MLFlow results
    └── logs/                          ← Training logs
```

---

## 🔧 Common Tweaks

### Make Training Faster
Edit `config/mlops_config.yaml`:
```yaml
n_estimators: 100  # Instead of 200 (less trees = faster)
drivers_to_simulate: 10  # Instead of 20 (fewer drivers)
trips_per_driver: 5  # Instead of 15 (fewer trips)
```

### Make Model More Accurate
```yaml
n_estimators: 300  # More trees = more accuracy
max_depth: 8  # Instead of 7 (deeper = more complex)
learning_rate: 0.03  # Instead of 0.05 (slower, more careful)
```

### Generate More Data
```yaml
drivers_to_simulate: 50  # More drivers
trips_per_driver: 30  # More trips per driver
# Result: 1,500 total trips (instead of 300)
```

---

## 📊 Understanding Results

### Good Results Look Like:
```
Test R² Score: 0.88 ✅
RMSE: 12.5
MAE: 9.2
Cross-Validation R²: 0.876 ± 0.023
Quality Gate: PASSED ✅
```

### What Each Metric Means:

| Metric | Range | Good | Bad |
|--------|-------|------|-----|
| **R² Score** | 0.0-1.0 | >0.85 | <0.70 |
| **RMSE** | 0-100 | <20 | >30 |
| **MAE** | 0-100 | <15 | >25 |

---

## 🤔 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "python: command not found" | Install Python from python.org |
| "ModuleNotFoundError" | Run `pip install mlflow xgboost scikit-learn pandas numpy` |
| Training takes forever | Reduce `n_estimators` in config.yaml |
| MLFlow UI won't open | Try: `mlflow ui --port 5001` |
| Can't find file | Check you're in right directory: `cd tracedata-candidate` |

---

## 🚀 Minimal Quick Start (5 min)

```bash
# 1. Install
pip install mlflow xgboost scikit-learn pandas numpy

# 2. Run
python -m src.mlops.training_pipeline

# 3. View
mlflow ui
# Go to: http://localhost:5000
```

Done! Your model is trained! 🎉

---

## 📚 Learning Path

**Day 1:** 
- Read README.md
- Run training
- View results in MLFlow

**Day 2:**
- Read GETTING_STARTED.md
- Change one value in config.yaml
- Train again, compare results

**Day 3:**
- Read ARCHITECTURE.md
- Browse the code
- Try doc/FEATURE_ENGINEERING.md examples

**Day 4:**
- Read docs/MLOPS_GUIDE.md
- Experiment with different settings
- Compare runs in MLFlow UI

**Day 5:**
- Read docs/SHAP_EXPLAINABILITY.md
- Understand why model predicts what it does
- Ready to use on real data!

---

## 💡 Quick Concepts

### Machine Learning (30 seconds)
Instead of writing rules, you give examples. Computer finds the pattern.

### XGBoost (1 minute)
Algorithm that uses 200 small decision trees voting. Each tree looks at different aspects of data. Votes combined for final answer.

### MLFlow (1 minute)
Tool that remembers all your experiments. Like lab notebook for ML.

### Features (1 minute)
Measurements we use to predict smoothness:
- Speed changes (jerk)
- Harsh braking counts
- Turning forces
- Engine RPM
(18 total)

### Training (1 minute)
Process of showing computer examples so it learns to predict.

### Model (1 minute)
The "trained computer" that can now predict smoothness for new drivers.

---

## ⏱️ Expected Times

| Task | Time |
|------|------|
| Install packages | 2-5 min |
| Run training (first time) | 2-3 min |
| View MLFlow results | 1 min |
| Change config and retrain | 2-3 min |
| Read all documentation | 45-60 min |
| Understand entire system | 1-2 hours |

---

## 🎯 Success Checklist

- [ ] Python installed (`python --version` shows 3.9+)
- [ ] Packages installed (`pip list` shows mlflow, xgboost)
- [ ] Training runs successfully (R² ≥ 0.85)
- [ ] MLFlow UI works at localhost:5000
- [ ] Can modify config.yaml and retrain
- [ ] Understand what each metric means
- [ ] Know where to find documentation
- [ ] Ready to experiment!

---

## 🔗 Key Files to Remember

- **To run training:** `python -m src.mlops.training_pipeline`
- **To change settings:** Edit `config/mlops_config.yaml`
- **To browse code:** Open `src/core/smoothness_ml_engine.py`
- **To see results:** Run `mlflow ui`
- **To read about features:** See `docs/FEATURE_ENGINEERING.md`
- **To understand predictions:** Read `docs/SHAP_EXPLAINABILITY.md`

---

## 📞 "I Don't Know What to Do"

1. Re-read GETTING_STARTED.md (it's step-by-step)
2. Check ARCHITECTURE.md (explains the big picture)
3. Look for your question in FAQ section of docs
4. Check code comments (every function has explanation)
5. Try it anyway - best learning is by doing!

---

## ✨ You've Got This!

Every ML engineer started exactly where you are. You're doing amazing! 🚀

