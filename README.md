# Market Researcher Agentic

An agentic market-research desk: describe what you want to know and a team of agents
**plans → collects data → analyses → writes → reviews** a full research brief, streamed live to a dashboard.

## Features
- **Multi-agent pipeline** — Planner, Collector (parallel price/indicator/news fetch), Analyst (momentum, sentiment, SWOT, risk register), Writer, Reviewer.
- **Pluggable intelligence** — Claude via `ANTHROPIC_API_KEY`; without a key (or on any LLM failure/invalid output) a deterministic rule engine produces the report, so the app always works.
- **Live data** — Yahoo Finance prices, Google News RSS headlines. If unreachable, deterministic *demo data* is used and every view is clearly badged.
- **Dashboard UI** — market overview, live agent timeline (SSE), interactive price charts with SMA overlays, head-to-head tables, SWOT, risks, sentiment, watchlist, market explorer, Markdown/JSON export, print.
- **Scalable backend** — async FastAPI, DB-backed job queue with atomic claims (any number of replicas share one DB), SSE served from the event log, TTL cache with request coalescing, SQLite → PostgreSQL via `DATABASE_URL`, optional API-key auth and rate limiting.

## Quick start
```bash
# backend
cd backend && python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # optionally add ANTHROPIC_API_KEY
uvicorn app.main:app --reload   # http://localhost:8000/docs

# frontend (dev server proxies /api to :8000)
cd frontend && npm install && npm run dev   # http://localhost:5173
```
Production: `npm run build` in `frontend/` and the backend serves `frontend/dist` itself, or use Docker:
```bash
docker compose up --build       # app + PostgreSQL on :8000
```

## Tests
```bash
cd backend && pytest
```

## API (prefix `/api`)
`POST /research` · `GET /research` · `GET /research/{id}` · `GET /research/{id}/stream` (SSE) · `GET /research/{id}/export?format=md|json` · `POST /research/{id}/retry` · `DELETE /research/{id}` · `GET /market/{overview,search,quote/{s},history/{s}}` · `GET|POST|DELETE /watchlist` · `GET /dashboard/stats` · `GET /health` · `GET /config`

## Layout
```
backend/app/{agents,data,llm,services,api}   pipeline, market/news/indicators, LLM providers, job runner, routes
frontend/src/{pages,components,lib}          React + TS + Tailwind + Recharts
```
*Not investment advice.*
