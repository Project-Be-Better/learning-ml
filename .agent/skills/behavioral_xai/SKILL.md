---
name: behavioral_xai
description: Guidelines for maintaining the Bidirectional XAI, Fairness architecture, and the Domain-Driven Behavior Agent layer.
---

# Behavioral XAI & Fairness Skill

This skill provides the architectural blueprints and implementation standards for the **TraceData Scoring System**, specifically focusing on the intersection of Explainable AI (XAI), Fairness, Event-Driven Ingestion, and Multi-Agent Architecture.

## 1. Core Philosophy: "Transparency over Mitigation"
We do not silently adjust scores for fairness. Instead, we provide **Bidirectional Context**:
- **XAI (Physics)**: Explains *why* a score was given based on telemetry.
- **Fairness (Context)**: Explains *how* that score compares to the driver's demographic or experience cohort.

## 2. Multi-Container & Dual Ingestion Architecture
The system utilizes a **Distributed Multi-Container Architecture (Celery + Redis)** to decouple fast API reads from heavy ML/LLM workloads:

- **High-Velocity Pipeline (Telemetry)**: Simulator or IoT devices push raw telemetry payloads *directly* into the **Redis Broker**, bypassing the API.
- **Low-Velocity Pipeline (Feedback/Reviews)**: The Driver App sends HTTP POST requests to `core-api` (FastAPI), which acknowledges the request and enqueues a standard Celery task to Redis.
- **`agent-worker` (Celery)**: Consumes both the high-volume stream and the standard feedback queue. It runs XGBoost scoring, extracts XAI, and triggers the LLM narrative computation in the background, writing the final intelligence to the database.

## 3. Domain-Driven Design (DDD) for Agents
As the system scales to multiple agents (e.g., Behavior, Concierge, Places), agents must be strictly encapsulated using **Domain-Driven Design (DDD)** principles within the `src/agents/` directory:

```text
src/agents/
└── behavior/          # The Domain Boundary
    ├── __init__.py
    ├── agent.py       # Core Langchain/Gemini LLM logic
    └── tasks.py       # Celery asynchronous bindings and background tasks
```
**Rule**: Do not place monolithic agent scripts in the root `src/agents/` folder. Each agent must own its individual prompts, specific schemas, and Celery tasks within its designated domain subset.

## 4. The Behavior Agent Narrative Pattern
The `BehaviorAgent` must synthesize JSON data into human-readable narratives asynchronously.
- **Feature Filtering**: Always filter out non-behavioral statistical metadata: `ignored_features = {"base_value"}`
- **Professional Coaching Tone**: Use a supportive, coach-like tone that highlights performance relative to cohorts (e.g., "You are outperforming your cohort by X points... Your success is driven by your excellent consistency").

## 5. Database Schema Standards
Always maintain the following columns in both `trips` and `drivers` tables:
| Column | Type | Purpose |
| :--- | :--- | :--- |
| `explanation_json` | TEXT/JSON | XAI data (SHAP values). |
| `fairness_metadata_json` | TEXT/JSON | Performance relative to cohort (diff, avg). |
| `coaching_narrative` | TEXT | Final output from the Behavior Agent. |

## 6. Verification Workflow
To verify the entire asynchronous pipeline:
1. Initialize the database: `uv run python -m src.utils.simulator`
2. Extract features: `uv run python -m src.utils.processor`
3. Train the XGBoost model: `uv run python -m src.utils.trainer`
4. Score trips & generate XAI: `uv run python -m src.utils.scoring`
5. Calculate fairness metrics: `uv run python -m src.utils.fairness`
6. Start the distributed stack: `docker-compose up -d`
7. Verify results against the API: `GET /driver/{id}`
