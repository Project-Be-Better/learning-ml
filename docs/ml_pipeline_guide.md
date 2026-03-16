# TraceData ML Pipeline: A Ground-Level Technical Guide

> **For:** Engineers familiar with software systems who are new to ML, MLOps, and production deployment.
> **Goal:** Map every ML concept to a concrete file or function in this codebase.

---

## 🗺️ The Big Picture

The entire system is an **ML-powered Factory Line**: raw sensor data goes in, and an intelligent driver coaching report comes out. Here is everything, end to end:

```mermaid
flowchart LR
    subgraph "🏭 THE FACTORY LINE"
        direction LR
        A["📡 Vehicle Telemetry\n(Raw Sensor Data)"] --> B["⚙️ Feature Engineering\n(Physics → Numbers)"]
        B --> C["🤖 ML Model\n(Numbers → Score)"]
        C --> D["🔍 XAI Engine\n(Why that Score?)"]
        C --> E["⚖️ Fairness Auditor\n(Is it Biased?)"]
        D --> F["🧠 Behavior Agent\n(JSON → Human Language)"]
        E --> F
        F --> G["📊 Driver Dashboard\n(Final Report)"]
    end
```

---

## Stage 1: Data — Where It All Begins

### What is Telemetry?
Telemetry is a time-series stream of raw sensor readings from a moving vehicle. Each packet contains a timestamp, GPS coordinate, speed, and acceleration.

```mermaid
timeline
    title A 5-Minute Trip (One Reading Per 30s)
    00m00s : speed=45 kmh, accel=0.2
    00m30s : speed=72 kmh, accel=1.8
    01m00s : speed=68 kmh, accel=-0.4
    01m30s : speed=90 kmh, accel=2.2
    02m00s : speed=85 kmh, accel=-1.6
    02m30s : speed=60 kmh, accel=-2.1
```

### The Database Schema
We store this time-series in a **Row-Oriented** schema (ADR 001). Each GPS reading is one database row — not a JSON blob.

```mermaid
erDiagram
    DRIVERS {
        int driver_id PK
        string name
        float smoothness_avg
        float safety_avg
        float overall_avg
        int trip_count
        json explanation_json
        json fairness_metadata_json
        text coaching_narrative
    }
    TRIPS {
        int trip_id PK
        int driver_id FK
        datetime start_time
        datetime end_time
        float distance_km
        float smoothness_score
        float safety_score
        json explanation_json
        json fairness_metadata_json
    }
    TELEMETRY_POINTS {
        int point_id PK
        int trip_id FK
        datetime timestamp
        float speed_kmh
        float acceleration_ms2
        float lat
        float lon
    }

    DRIVERS ||--o{ TRIPS : "has many"
    TRIPS ||--o{ TELEMETRY_POINTS : "captured as"
```

---

## Stage 2: Feature Engineering — Translating Physics into Numbers

This is the **most important and most human** step in ML. The model cannot understand "jerky driving" — it only sees columns of numbers. Feature Engineering is the act of encoding your domain knowledge into those columns.

```mermaid
flowchart TD
    subgraph "RAW INPUT: List of Acceleration Values"
        R["[0.2, 1.8, -0.4, 2.2, -1.6, -2.1]"]
    end

    subgraph "FEATURE EXTRACTION (features.py)"
        F1["Jerk = Change in Accel\n[1.6, -2.2, 2.6, -3.8, -0.5]"]
        F2["std_dev(Jerk)\n= accel_fluidity = 2.1"]
        F3["std_dev(Accel)\n= driving_consistency = 1.7"]
        F4["% of readings in [-0.5, +0.5]\n= comfort_zone_percent = 33%"]
    end

    subgraph "MODEL INPUT: Feature Row"
        M["{ accel_fluidity: 2.1,\n  driving_consistency: 1.7,\n  comfort_zone_percent: 33.0 }"]
    end

    R --> F1 --> F2
    R --> F3
    R --> F4
    F2 --> M
    F3 --> M
    F4 --> M
```

### Intuition Behind Each Feature

| Feature | Formula | Low Value Means | High Value Means |
| :--- | :--- | :--- | :--- |
| **`accel_fluidity`** | `std_dev(Δ acceleration)` | Smooth, gradual transitions | Jerky, sudden changes |
| **`driving_consistency`** | `std_dev(acceleration)` | Predictable, steady pace | Erratic, unpredictable |
| **`comfort_zone_percent`** | `% where |accel| ≤ 0.5` | Rarely in comfort zone | Nearly always gentle |

> **Key Insight:** The model sees these 3 numbers, not GPS coordinates or timestamps. You are the translator between physics and mathematics.

---

## Stage 3: ML Training — Teaching the Model to Score

Training happens **offline, once** (or periodically). It produces a `.joblib` artifact that is then used at runtime.

```mermaid
flowchart LR
    subgraph "OFFLINE: TRAINING (trainer.py)"
        direction TB
        TD["Training Data\n(thousands of trips)"] --> FE["Features\n[fluidity, consistency, comfort]"]
        FE --> XG["XGBoost\nRegressor.fit()"]
        Labels["Labels\n(smoothness_score)"] --> XG
        XG --> ART["models/smoothness_model.joblib\n(The ML Artifact)"]
    end

    subgraph "ONLINE: INFERENCE (scoring.py)"
        direction TB
        NR["New Trip\n(never seen before)"] --> NFE["Feature Extraction"]
        ART2["models/smoothness_model.joblib"] --> P["model.predict(features)"]
        NFE --> P
        P --> SC["Smoothness Score\n(e.g., 73 / 100)"]
    end

    ART -.-> |"Loaded at startup"| ART2
```

### The Training Loop (Simplified)

```mermaid
sequenceDiagram
    participant T as trainer.py
    participant DB as SQLite DB
    participant XG as XGBoost Model
    participant FS as File System

    T->>DB: SELECT feature triplets
    DB-->>T: Rows with [fluidity, consistency, comfort]
    T->>T: Build X (features) and y (labels) arrays
    T->>XG: model.fit(X_train, y_train)
    Note over XG: The model finds the mathematical<br/>relationship between features and scores
    XG-->>T: Trained model object
    T->>FS: joblib.dump(model, "models/smoothness_model.joblib")
    Note over FS: The "learned knowledge" is frozen to disk
    T->>XG: model.score(X_test, y_test)
    XG-->>T: R² = 0.97 ✅
```

---

## Stage 4: Inference — Scoring a New Trip at Runtime

"Inference" = using the trained model to generate predictions on **new, unseen data**.

```mermaid
flowchart TD
    subgraph "POST /score-trip"
        T["New Telemetry\nfrom IoT → Redis"] --> FE["features.py\nextract_features()"]
        FE --> INF["scoring.py\nmodel.predict(features)"]
        INF --> SS["Smoothness Score\n(0-100)"]
        T --> SF["Safety Rules Engine\n(scoring.py)"]
        SF --> SAF["Safety Score\n(0-100)"]
        SS --> C["Composite Score\n(0.6 * smooth + 0.4 * safety)"]
        SAF --> C
        C --> DB["Write to DB\n(trips table)"]
    end
```

### Why Hybrid? ML + Rules?

```mermaid
quadrantChart
    title "ML vs Rules: When to Use Which"
    x-axis "Subjective ←——→ Objective"
    y-axis "Low Impact ←——→ High Impact"
    quadrant-1 "ML Required"
    quadrant-2 "LLM / Human"
    quadrant-3 "Heuristics OK"
    quadrant-4 "Hard Rules"
    "Smoothness Score": [0.25, 0.85]
    "Harsh Braking Penalty": [0.55, 0.6]
    "Speed Limit Violation": [0.95, 0.9]
    "Comfort Prediction": [0.15, 0.4]
    "Journey Planning": [0.2, 0.65]
```

Speeding is **objective** (you either exceeded the limit or you didn't). You don't need ML to detect it — you need a rule. Smoothness is **subjective** (what feels smooth to one person differs from another). That's where ML shines.

---

## Stage 5: Explainability (XAI) — Opening the Black Box

XGBoost is a black box. SHAP reverse-engineers its decisions.

```mermaid
flowchart LR
    subgraph "BLACK BOX"
        IN["[fluidity=2.1,\n consistency=3.8,\n comfort=25.8]"] --> MODEL["XGBoost\n🔮"]
        MODEL --> OUT["Score: 62"]
    end

    subgraph "SHAP EXPLANATION (explain.py)"
        BV["Base Value: 67.1\n(model's average starting point)"]
        F1["accel_fluidity: -5.0\n⬇ Hurts score"]
        F2["driving_consistency: +3.8\n⬆ Helps score"]
        F3["comfort_zone_percent: -3.9\n⬇ Hurts score"]
        FINAL["Final Score: 62 = 67.1 - 5.0 + 3.8 - 3.9"]
    end

    OUT -.->|"SHAP unpacks the math"| BV
    BV --> FINAL
    F1 --> FINAL
    F2 --> FINAL
    F3 --> FINAL
```

### Bidirectional XAI: Two Levels of Explanation

```mermaid
graph TD
    subgraph "TRIP LEVEL (Local Explanation)"
        TE["Trip #47: Score = 62"]
        TE --> TS["SHAP: accel_fluidity -5.0\ndriving_consistency +3.8\ncomfort_zone_percent -3.9"]
        TS --> TQ["Q: What happened on this specific trip?"]
    end

    subgraph "DRIVER LEVEL (Global Signature)"
        DE["Driver Ahmad: Avg Score = 74"]
        DE --> DS["Aggregate SHAP across 50 trips:\naccel_fluidity mean=-2.1\nconsistency mean=+4.5"]
        DS --> DQ["Q: What is Ahmad's overall driving signature?"]
    end
```

---

## Stage 6: Fairness — Is the Model Treating Everyone Equally?

```mermaid
flowchart TD
    subgraph "FAIRNESS AUDIT (fairness.py)"
        D["Driver Score: 98"]
        AG["Driver's Age Group\n(e.g., 61-70 years)"]
        DB2["All drivers in\nage group 61-70"]
        DB2 --> AVG["Cohort Average: 68.15"]
        D --> DIFF["diff = 98 - 68.15 = +29.85"]
        AVG --> DIFF
        DIFF --> STATUS["Status: Outperforming ✅"]
        STATUS --> META["fairness_metadata_json:\n{ age_cohort_avg: 68.15, diff: +29.85 }"]
    end
```

### The Fairness Philosophy: Context, Not Correction

```mermaid
stateDiagram-v2
    state "Score Generated" as S
    state "Fairness Check" as FC
    state "Has Bias Signal?" as HBS
    state "Adjust Score" as AS
    state "Add Context" as AC
    state "TraceData Approach ✅" as TA
    state "Alternative Approach ❌" as AA

    S --> FC
    FC --> HBS
    HBS --> AA : Yes → secretly penalize
    AA --> AS : adjust down
    HBS --> TA : Yes → show context
    TA --> AC : explain cohort
    note right of AC : "You're outperforming\nyour age group by\n29.86 points"
    note right of AS : User never knows.\nTrust is lost.
```

---

## Stage 7: The Behavior Agent — The Last Mile of Intelligence

The Agent layer converts raw JSON intelligence into a human coaching report.

```mermaid
flowchart TD
    subgraph "INPUTS (from DB)"
        XAI["XAI Data\n{accel_fluidity: 3.8,\n consistency: 1.28}"]
        FAIR["Fairness Data\n{cohort_avg: 68.15, diff: +29.86}"]
    end

    subgraph "BEHAVIOR AGENT (src/agents/behavior/agent.py)"
        B1["1. Filter ignored features\n(remove 'base_value')"]
        B2["2. Find top SHAP feature\n(e.g., driving_consistency = 3.8)"]
        B3["3. Determine fairness status\n(diff > 0 → outperforming)"]
        B4["4. Compose narrative using\nheuristic template (or LLM later)"]
    end

    subgraph "OUTPUT"
        NAR["'Based on your recent trips, you are\noutperforming your age cohort by 29.86 points.\nYour success is driven by your excellent\ndriving consistency.'"]
    end

    XAI --> B1 --> B2
    FAIR --> B3
    B2 --> B4
    B3 --> B4
    B4 --> NAR
```

---

## Stage 8: MLOps — The End-to-End Deployment Architecture

This is the full production system showing how all components interact.

```mermaid
C4Context
    title System Context for TraceData ML Platform
    Person(driver, "Driver", "Uses the TraceData mobile app")
    System(tracedata, "TraceData Platform", "Multi-container ML scoring system")
    System_Ext(iot, "Vehicle IoT Device", "Publishes raw telemetry")
    Rel(driver, tracedata, "Views coaching report, submits feedback")
    Rel(iot, tracedata, "Streams telemetry directly to Redis")
```

```mermaid
flowchart TB
    subgraph "IoT / Simulator Layer"
        IOT["📡 IoT Device / simulator.py"]
    end

    subgraph "Infrastructure Layer (docker-compose.yml)"
        REDIS["🔴 Redis\nBroker + Stream"]
        subgraph "core-api (FastAPI)"
            API["POST /feedback\nGET /driver/{id}"]
        end
        subgraph "agent-worker (Celery)"
            WORKER["⚙️ Celery Worker\n• Feature Engineering\n• XGBoost Inference\n• SHAP/Fairness\n• Behavior Agent"]
        end
        DB[("🗄️ SQLite / PostgreSQL")]
    end

    subgraph "Frontend / Dashboard"
        FE["📱 Driver App"]
    end

    IOT -->|"Direct push (high-velocity)"| REDIS
    FE -->|"POST /feedback"| API
    API -->|"enqueue(FeedbackTask)"| REDIS
    REDIS -->|"Dequeue task"| WORKER
    WORKER -->|"Write scores,\nXAI, narrative"| DB
    FE -->|"GET /driver/{id}"| API
    API -->|"Read pre-computed report"| DB
    DB -->|"Return dashboard data"| API
```

### Container Scaling Model

```mermaid
graph TD
    subgraph "Scale horizontal for traffic"
        A1["core-api replica 1"]
        A2["core-api replica 2"]
        A3["core-api replica 3"]
    end
    subgraph "Scale horizontal for ML throughput"
        W1["agent-worker replica 1"]
        W2["agent-worker replica 2"]
    end
    REDIS2["🔴 Redis"] --> W1
    REDIS2 --> W2
    LB["Load Balancer"] --> A1
    LB --> A2
    LB --> A3
```

---

## End-to-End Data Flow: The Complete Journey

```mermaid
sequenceDiagram
    participant IOT as IoT Sensor
    participant Redis as Redis Broker
    participant Worker as Celery Worker
    participant FE as Feature Engine
    participant XG as XGBoost Model
    participant SHAP as SHAP Engine
    participant FA as Fairness Auditor
    participant BA as Behavior Agent
    participant DB as Database
    participant API as FastAPI (core-api)
    participant App as Driver App

    Note over IOT,Redis: Phase 1: High-Velocity Ingestion
    IOT->>Redis: push({ driver_id, trip_id, telemetry[] })

    Note over Redis,Worker: Phase 2: Background Processing
    Redis->>Worker: consume task
    Worker->>FE: extract_features(telemetry)
    FE-->>Worker: {fluidity=2.1, consistency=3.8, comfort=25.8}
    Worker->>XG: model.predict(features)
    XG-->>Worker: smoothness_score = 73
    Worker->>Worker: apply_safety_rules(telemetry)
    Worker-->>Worker: safety_score = 100
    Worker->>SHAP: explain(trip_id, features)
    SHAP-->>Worker: explanation_json
    Worker->>FA: audit(driver_id, score)
    FA-->>Worker: fairness_metadata_json
    Worker->>BA: generate_narrative(driver_id)
    BA-->>Worker: coaching_narrative (text)
    Worker->>DB: UPDATE drivers SET coaching_narrative, explanation_json

    Note over API,App: Phase 3: Frontend Read (Lightning Fast)
    App->>API: GET /driver/1
    API->>DB: SELECT * FROM drivers WHERE driver_id=1
    DB-->>API: Pre-computed profile
    API-->>App: { score, xai, fairness, coaching_narrative }
```

---

## 📂 Codebase Map

```mermaid
graph TD
    subgraph "src/core/ — The Engine"
        CFG["config.py\nCentralized paths"]
        FT["features.py\nPhysics extraction"]
        SC["scoring.py\nML + Rules orchestrator"]
        EX["explain.py\nSHAP/LIME"]
        FA["fairness.py\nBias auditing"]
        CA["celery_app.py\nTask queue config"]
    end

    subgraph "src/agents/behavior/ — The Agent Domain"
        AG["agent.py\nHeuristic + LLM narrative"]
        TK["tasks.py\nCelery async bindings"]
    end

    subgraph "src/utils/ — Operational Scripts"
        SIM["simulator.py\nDB init + synthetic data"]
        TR["trainer.py\nXGBoost training"]
        PR["processor.py\nBatch feature extraction"]
        CL["cleanup_db.py\nDB maintenance"]
    end

    subgraph "Root — Entrypoints & Config"
        MAIN["main.py\nFastAPI application"]
        DC["docker-compose.yml\nContainer orchestration"]
        PY["pyproject.toml\nudependencies"]
        MOD["models/\nML artifacts (.joblib)"]
    end

    MAIN --> SC
    MAIN --> TK
    TK --> AG
    SC --> FT
    SC --> EX
    SC --> FA
    TR --> MOD
    SC --> MOD
    SIM --> CFG
    TR --> CFG
    SC --> CFG
```

---

## 🎓 Glossary for the ML-Curious Engineer

| Term | Software Analogy | TraceData Equivalent |
| :--- | :--- | :--- |
| **Training** | Compiling code | `trainer.py` run |
| **Model Artifact** | `.jar` / `.dll` binary | `models/smoothness_model.joblib` |
| **Inference** | Calling a function | `model.predict(features)` in `scoring.py` |
| **Feature Engineering** | Data transformation | `src/core/features.py` |
| **SHAP** | Stack trace for model decisions | `explain.py` |
| **MLOps** | DevOps for ML models | `docker-compose.yml` + Celery |
| **Drift** | Memory leak / regression | Model accuracy degrading over time (future monitoring) |
| **Synthetic Data** | Unit test mocks | `src/utils/simulator.py` |
