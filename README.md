# MusicPulse AI RAG — Complete Project

This package contains:

- `musicpulse-mvp/`: FastAPI, PostgreSQL, Redis, Celery, YouTube ingestion, analytics, RAG, LLM integration, tests, and backend documentation.
- `musicpulse-frontend/`: React dashboard, conversational RAG assistant, evidence display, conversation history, knowledge manager, and ingestion controls.
- `TEST_REPORT.md`: Validation results recorded before packaging.

Start with `musicpulse-mvp/README.md`, then use `musicpulse-frontend/README.md` for the interface setup.


## AI providers

- **Generation:** Google Gemini (`gemini-2.5-flash`) through the Gemini REST API.
- **Embeddings:** local `BAAI/bge-small-en-v1.5` through sentence-transformers.
- **Fallback:** deterministic SQL analytics and hash embeddings keep the application usable during provider or model-download failures.
