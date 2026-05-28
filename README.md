# FINIX AI

> Multi-agent financial intelligence system. Markets are chaos. FINIX rises above it.

---

## Architecture

```
User Query
    ↓
FINIX (Master Orchestrator)
    ↓
Workflow Selection (Research / Decision)
    ↙           ↘
ROME            KOVA
(API fetcher)   (Market intelligence)
    ↘           ↙
     Broker Call → ONE Gemini API call
    ↙           ↘
KOVA result    FINIX synthesis
                ↓
            Final Response
                ↓
            FRANK (stores result)
```

## Agents

| Agent | Role |
|-------|------|
| FINIX | Master orchestrator |
| ROME  | API broker — fetches data, never reasons |
| KOVA  | Market intelligence — interprets data |
| DIMON | Financial reasoning — (Phase 2) |
| FRANK | Persistent memory service |

## Stack

- **Backend**: Python + FastAPI
- **AI**: Gemini 2.5 Flash
- **Memory**: Supabase (PostgreSQL)
- **Market Data**: yfinance + CoinGecko
- **News**: NewsAPI
- **Hosting**: Render

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo>
cd finix-core
pip install -r requirements.txt
```

### 2. Environment variables

```bash
cp .env.example .env
# Fill in your keys
```

### 3. Run locally

```bash
python main.py
# Server at http://localhost:8000
```

### 4. Test

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Analyze Nvidia stock", "user_id": "test_user"}'
```

---

## Build Phases

- [x] Phase 1 — Project foundation & skeleton
- [x] Phase 2 — Agent framework (FINIX, ROME, KOVA, FRANK stubs)
- [x] Phase 3 — Rome implementation (market + news fetch)
- [x] Phase 4 — Kova implementation (market intelligence)
- [x] Phase 5 — FINIX orchestration
- [x] Phase 6 — Research workflow MVP
- [ ] Phase 7 — Frank + Supabase persistent memory
- [ ] Phase 8 — Decision workflow + Dimon
- [ ] Phase 9 — External API (for June integration)
- [ ] Phase 10 — Frontend

---

## API

### POST /api/query
```json
{
  "query": "Should I buy Bitcoin right now?",
  "user_id": "your_user_id",
  "context": {}
}
```

### GET /health
UptimeRobot monitoring endpoint.

---

*This is not financial advice.*
