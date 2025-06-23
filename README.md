# Adaptive Insight Engine (AIE)

AIE is a modular, extensible GenAI multi-agent system built with Google Cloud's Agent Development Kit (ADK), Streamlit, and best-in-class Python libraries. It is designed for rapid prototyping, enterprise-grade deployment, and seamless integration with Google Cloud services (Vertex AI, Agent Engine, Cloud Run, and more).

---

## Architecture Overview

- **Agents**: Modular Python classes, each with a clear responsibility (see below).
- **Tools**: Data processing, analysis, and simulation modules, deployable locally or on Cloud Run.
- **Interfaces**: Web app (Streamlit), REST API (FastAPI), and stubs for MCP/A2A protocols.
- **Data**: Supports CSV, PDF, TEXT.
- **Cloud Native**: Deployable locally, on Cloud Run, Vertex AI, or any cloud.
- **Logging & Traceability**: Structured logging and ExplanationTracerAgent for full auditability.

---

## Directory Structure

```
adaptive_insight_engine/
│
├── adaptive_insight_engine/                  # All agent classes (UserInteractionAgent, etc.)
├── tools/                   # Data processing, analysis, simulation tools
├── interfaces/              # Web, REST, MCP, A2A protocol handlers
├── utils/                   # Shared utilities (logging, config, etc.)
├── deployment/              # Docker, cloud deployment scripts
├── tests/                   # Unit and integration tests
├── README.md
├── pyproject.toml
└── .env-example
```

---

## Agent Roles

- **UserInteractionAgent**: Orchestrates user interactions, manages UI/API, validates inputs, and initiates workflows.
- **WorkflowOrchestratorAgent**: Manages the sequence of analysis tasks based on user selections.
- **DataIngestionAgent**: Handles data intake, cleaning, and storage (CSV, PDF, TEXT).
- **ExternalContextAgent**: Fetches and merges external public data (APIs, public datasets).
- **CoreAnalysisAgent**: Performs core data analysis and correlation.
- **QueryUnderstandingAgent**: Interprets user follow-up queries using GenAI (Gemini/Vertex AI).
- **SimulationAgent**: Runs 'what-if' scenario simulations.
- **InsightSynthesisAgent**: Synthesizes insights and generates narratives using GenAI.
- **ExplanationTracerAgent**: Collects logs and provides traceable explanations for all insights.

---

## Key Features

- **Streamlit Web App**: Interactive UI for file upload, parameter selection, and results.
- **REST API**: All workflows accessible via FastAPI endpoints.
- **Extensible Protocols**: Stubs for MCP and A2A for future multi-agent interoperability.
- **Cloud Integration**: Native support for Google Cloud Storage, Vertex AI, and more.
- **Best-in-Class Libraries**: pandas, numpy, scikit-learn, statsmodels, google-cloud-*, structlog, etc.
- **Structured Logging**: All agent actions and data flows are logged for monitoring and evaluation.
- **Deployment Ready**: Dockerized, with scripts for local and cloud deployment.

---

## Getting Started

1. **Clone the repo**
2. **Install dependencies**: If using Poetry, run `poetry install`. If using pip, run `pip install -r requirements.txt`.
3. **Set up environment variables**: Copy `.env-example` to `.env` and fill in your credentials.
4. **Run locally**:
   - Streamlit UI: `streamlit run interfaces/streamlit_app.py` or `poetry run run-streamlit`
   - REST API: `uvicorn interfaces.rest_api:app --reload` or `poetry run run-api`
5. **Deploy to Cloud Run/Vertex AI**: See `deployment/` for scripts and instructions.

---

## Extensibility & Customization

- **Add new agents**: Create a new class in `adaptive_insight_engine/` and register it in the orchestrator.
- **Add new tools**: Implement in `tools/` and expose to agents as needed.
- **Integrate new data sources**: Extend `DataIngestionAgent` and `ExternalContextAgent`.
- **Support new protocols**: Implement handlers in `interfaces/`.

---

## References

- [Vertex AI multi-agent systems overview](https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai)
- [Agent Development Kit (ADK)](https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/)
- [Top Python Libraries](https://www.mygreatlearning.com/blog/open-source-python-libraries/)
- [AIE - Tools & Technologies](https://googlecloudmultiagents.devpost.com/resources)
- [AIE - Requirement & Solution approach](https://docs.google.com/document/d/1sNx3vxHOCMaqLYT0Q_MMUi0jQHX1Y0VzN9OQYThEfmA/edit?tab=t.aqubdcohfh36)

---

## License

MIT
