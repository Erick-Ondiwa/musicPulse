# MusicPulse AI Frontend

React interface for the RAG-powered MusicPulse backend.

## Features

- Music analytics dashboard and charts
- Trending, latest, and most-viewed rankings
- Multi-turn RAG assistant with SQL evidence and retrieved sources
- Provider/fallback indicators
- Persistent conversation history
- RAG knowledge-base synchronization and manual document upload
- YouTube ingestion controls

## Setup

1. Start the backend from the `musicpulse-mvp` folder.
2. Create the frontend environment file:

```powershell
Copy-Item .env.example .env
```

3. Confirm `.env` contains:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

4. Install and run:

```powershell
npm install
npm run dev
```

Open `http://localhost:5173`.

## Production build

```powershell
npm run build
npm run preview
```

## Important security rule

Only the backend stores `GEMINI_API_KEY` and `YOUTUBE_API_KEY`. Vite variables are delivered to the browser, so secret keys must never be placed in the frontend `.env`.
