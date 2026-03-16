# TraceData ML Scoring Service

Production-grade vehicle telemetry analysis system for **TraceData MK-IV**.

## 🏗️ Architecture
The system is built as a **Modular Monolith** with a dedicated **Behavior Agent** for explainable AI and fairness auditing.

```
tracedata-platform/
└── ai-agents/ (learning-ml)
    ├── src/
    │   ├── core/      # Scoring, XAI, Fairness, Features
    │   ├── agents/    # Behavior (Scoring) Agent
    │   └── utils/     # Ingestion, ML Training, Simulation
    ├── models/        # Joblib artifacts
    ├── docs/          # Technical deep-dives
    └── main.py        # FastAPI Entry point
```

## 🚀 Getting Started
1. **Setup**: `uv sync`
2. **Initialize DB**: `uv run python -m src.utils.simulator`
3. **Run Service**: `uv run python main.py` or use `-m src.utils.simulator` (to run as module)

## 📊 Endpoints
- `POST /telemetry`: Ingest raw points
- `GET /driver/{id}`: Detailed profile with **Coaching Narratives**
- `POST /score-trip`: On-demand trip valuation

## 🧪 Documentation
For a full technical walkthrough, see [docs/walkthrough.md](file:///d:/learning-projects/learning-ml/docs/walkthrough.md).
