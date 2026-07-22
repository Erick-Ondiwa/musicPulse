# MusicPulse AI — RAG Music Intelligence Platform

MusicPulse AI collects YouTube music data, stores historical metrics, calculates explainable rankings, builds a searchable knowledge base, and answers natural-language questions with Retrieval-Augmented Generation (RAG).

The application works in two modes:

1. **Full AI mode:** an API-based LLM writes grounded answers from SQL analytics and retrieved documents.
2. **Safe fallback mode:** when no LLM key is configured or the provider is unavailable, deterministic analytics plus local retrieval still return valid answers.

## Architecture

```text
YouTube Data API
       |
       v
FastAPI / Celery ingestion
       |
       +--> PostgreSQL structured tables (artists, videos, metric snapshots)
       |
       +--> RAG knowledge documents + embeddings
                     |
User question --> SQL analytics + semantic retrieval
                     |
                     v
       Gemini generateContent API
                     |
                     v
Grounded answer + evidence + conversation history --> React frontend
```

## AI and RAG workflow

- **Structured retrieval:** exact numbers, rankings, dates, and growth come from SQLAlchemy analytics queries.
- **Semantic retrieval:** video descriptions, metadata, and manually added documents are embedded and ranked by cosine similarity.
- **Generation:** the LLM receives only retrieved evidence and approved analytics output.
- **Fallback:** if the API key is absent or a request fails, the deterministic answer is returned instead of an application error.
- **Auditability:** conversations, messages, provider selection, source IDs, and fallback status are stored in PostgreSQL.

## Main technologies

- FastAPI, Pydantic, SQLAlchemy, PostgreSQL
- Redis, Celery worker, Celery Beat
- YouTube Data API v3
- Google Gemini generateContent API
- Local BAAI/bge-small-en-v1.5 embeddings through sentence-transformers
- React, Vite, TanStack Query, Axios, Recharts
- Docker Compose and Pytest

## Project setup with Docker

### 1. Create `.env`

```powershell
Copy-Item .env.example .env
```

Add your YouTube key:

```env
YOUTUBE_API_KEY=your_youtube_key
```

For full LLM mode, also add:

```env
GEMINI_API_KEY=your_google_ai_studio_key
GEMINI_CHAT_MODEL=gemini-2.5-flash

# Local embeddings; no paid embeddings API key is needed.
BGE_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
BGE_DEVICE=cpu
RAG_EMBEDDING_DIMENSIONS=384
```

The Gemini key is optional. Without it, deterministic RAG remains available. Never put it in the frontend `.env`.

### 2. Start backend services

```powershell
docker compose down
docker compose up --build
```

Available services:

- API and Swagger: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

### 3. Seed demonstration data

```powershell
docker compose exec api python -m app.scripts.seed_demo
```

The seed command also generates RAG knowledge documents.

### 4. Synchronize existing videos into RAG manually

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/knowledge/sync-videos"
```

New and updated YouTube ingestion automatically synchronizes the knowledge base.

### 5. Run automated tests

```powershell
docker compose exec api pytest -q
```

Tests do not require a Gemini or YouTube key. They use SQLite, a mocked Gemini response, an injected BGE-compatible encoder, and deterministic fallback embeddings.

## Gemini and BGE configuration

MusicPulse uses Gemini only for final grounded language generation. Authentication is sent through the `x-goog-api-key` header to Gemini's `generateContent` REST endpoint. Exact metrics continue to come from SQL analytics.

`BAAI/bge-small-en-v1.5` runs locally through `sentence-transformers`; it does not consume Gemini quota and does not need an embeddings API key. The model outputs 384-dimensional vectors. The first use downloads approximately the model files from Hugging Face, after which Docker reuses the `huggingface_cache` volume.

If you previously indexed documents with the old 256-dimensional embedding configuration, rebuild them after startup:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/knowledge/sync-videos"
```

Existing documents with a different vector length are safely ignored during cosine comparison until they are re-indexed.

## Frontend setup

From the `musicpulse-frontend` folder:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Open `http://localhost:5173`.

Frontend `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Important API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health and LLM configuration status |
| POST | `/api/v1/assistant/ask` | Grounded conversational answer |
| GET | `/api/v1/assistant/conversations` | Conversation list |
| GET | `/api/v1/assistant/conversations/{id}` | Full message history |
| POST | `/api/v1/knowledge/sync-videos` | Rebuild video knowledge documents |
| GET | `/api/v1/knowledge/documents` | Inspect indexed knowledge |
| POST | `/api/v1/knowledge/documents` | Add a manual report or market note |
| GET | `/api/v1/songs/trending` | Explainable trend ranking |
| POST | `/api/v1/ingestion/popular` | Collect popular YouTube music |

## Example assistant request

```powershell
$body = @{
  question = "Which artists are gaining attention and why?"
  conversation_id = $null
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/assistant/ask" `
  -ContentType "application/json" `
  -Body $body
```

The response includes `answer`, `data`, `sources`, `provider`, `model_name`, `fallback_used`, and `conversation_id`.

## Add a manual knowledge document

```powershell
$body = @{
  title = "Kenya Music Market Note"
  content = "Afro-pop collaborations generated strong engagement during the monitored campaign."
  source_url = "https://example.com/report"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "http://localhost:8000/api/v1/knowledge/documents" `
  -ContentType "application/json" `
  -Body $body
```

## Viewing PostgreSQL

```powershell
docker compose exec db psql -U musicpulse -d musicpulse
```

Useful commands:

```sql
\dt
SELECT * FROM knowledge_documents LIMIT 10;
SELECT * FROM conversations ORDER BY created_at DESC;
SELECT * FROM assistant_runs ORDER BY created_at DESC;
```

## Production notes

- Restrict `CORS_ORIGINS` to real frontend domains.
- Use managed PostgreSQL and Redis, HTTPS, secret management, and authentication.
- For very large knowledge bases, replace Python-side cosine search with pgvector or a managed vector database.
- Evaluate answer quality using a fixed question set before changing models or prompts.
- Keep `GEMINI_API_KEY` only on the backend.
- The first BGE request downloads the model into the shared Hugging Face Docker cache.
- After changing embedding models or dimensions, run `/knowledge/sync-videos` to rebuild stored vectors.
