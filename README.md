# AGENSTOCK — AI Stock Research Agent

Comprehensive developer README. This file documents the project, architecture, folder layout, files, imports, design patterns, security, and how to run and extend the system.

---

## Introduction

AGENSTOCK is a conversational AI-driven stock research application built with FastAPI and Jinja2 templates. It aggregates market and fundamental data, computes technical indicators, synthesizes insights with LLMs, and produces interactive charts and printable PDF research reports.

This README contains a full reference for developers: features, file maps, module responsibilities, configuration, architecture diagrams, and step-by-step setup instructions for Windows.

## About the project

- Primary language: Python 3.10+
- Web framework: FastAPI
- Templating: Jinja2
- Charting: Plotly.js (client-side), mplfinance/matplotlib (server-side optional)
- PDF generation: ReportLab
- Data processing: pandas, numpy
- External data providers: yfinance, AlphaVantage, IndStock (for IN market), etc.

## Full feature list (user-facing)

- Conversational Research Agent (chat)
- Enhanced Research (multi-source aggregation + LLM summaries)
- Interactive Visual Analytics (candlesticks, SMA, RSI, MACD, Bollinger Bands)
- Portfolio Management (holdings, allocation, analysis)
- Stock Comparison (multi-ticker comparison)
- PDF Report Generation with bookmarks and two-column chart layout
- Export charts to PNG
- Persisted chart zoom/pan state (localStorage)
- In-memory TTL cache for heavy enhanced research payloads

## Folder skeleton 

```
app/
   ├─ templates/          # Jinja2 templates (html)
   ├─ static/
   │   ├─ css/
   │   └─ js/
   ├─ models/             # Pydantic models
   ├─ routes/             # FastAPI routers (api & pages)
   ├─ services/           # Business logic and external API integration
   ├─ utils/              # Helpers (pdf generator, security, rotating api keys)
   └─ main.py             # FastAPI app entrypoint

docs/
   ├─ diagrams/
   └─ screenshots/

tools/
   └─ screenshot_capture.py

requirements.txt
readme2.md
README.md
```

## Files table (selected important files)

| File | Purpose | Key functions/classes |
|---|---:|---|
| `app/main.py` | Application entry, route mounting | `landing_page`, `about_page`, `app` initialisation |
| `app/routes/research.py` | Research-related endpoints | `post_enhanced`, `post_enhanced_report`, `post_enhanced_report_pdf` |
| `app/services/stock_service.py` | Data aggregation, indicators, caching | `get_historical_data`, `get_enhanced_research`, `_sma`, `_rsi` |
| `app/services/research_report_service.py` | Orchestrates LLM and chart generation | `generate_full_research_report`, `_parse_llm_to_pydantic` |
| `app/utils/pdf_generator.py` | Server-side PDF composition and image embedding | `generate_enhanced_stock_report` |
| `app/templates/enhanced_research.html` | Visual analytics UI | JS hooks for Plotly rendering, controls, export |
| `app/templates/about.html` | About page, diagrams, demos | canvas simulation and diagram embeds |
| `app/static/js/about.js` | Demo animation and live poller | `pollEnhanced`, `renderLive` |

> Tip: run `rg "def " app/services | sed -n '1,200p'` locally to list functions if you want an automated map.

## Main imports and usage

- `fastapi` — lightweight async web framework with automatic OpenAPI.
- `uvicorn` — ASGI server for production/development.
- `jinja2` — server-side templating for rendering HTML pages.
- `pandas` / `numpy` — timeseries processing and numerical computation.
- `yfinance` / `AlphaVantage` — external market data providers.
- `aiohttp` — async HTTP client for multi-source API calls.
- `reportlab` / `PIL` / `matplotlib` / `mplfinance` — server-side chart rendering and PDF creation.
- `plotly` — client-side interactive charts and optional server-side image exports.
- `langchain` / LLM SDK — orchestrating LLM calls for summarization (if configured).
- `python-jose` / `passlib[bcrypt]` — JWT encoding/verification and password hashing.

## Backend core functionalities (detailed)

### 1) Data aggregation & indicators
- `get_historical_data(symbol, period)` picks the best provider (yfinance, IndStock, or AlphaVantage) and returns a `pandas.DataFrame` normalized to a common OHLC+Volume schema.
- Indicators: SMA (rolling mean), RSI (EWMA variant), MACD (12/26/9 via EMA differences), Bollinger Bands (std dev bands) — usually computed server-side and returned in `get_enhanced_research`.

### 2) Enhanced research and caching
- `get_enhanced_research(symbol, period)` builds a payload:
   - `overview` (company info)
   - `quote` (latest price/metrics)
   - `historical` (OHLC time series)
   - `indicators` (sma_20, sma_50, rsi_14)
   - `chart_series` and `ohlc`
   - `macd` & `macd_signal`
   - `sentiment`
- Caching: module-level in-memory TTL cache `_enhanced_cache` with key = `SYMBOL|period`. TTL is configurable via settings (default 60s). Per-key `asyncio.Lock` prevents duplicate concurrent fetches.

### 3) PDF report generation
- `generate_enhanced_stock_report(report_model, charts)` uses ReportLab to produce a printable PDF with:
   - Title & executive summary
   - Two-column chart sections with captions
   - High-resolution chart images (server-side generated) embedded as PNG
   - Table-of-contents (bookmarks)

### 4) Authentication & security
- JWT-based tokens (python-jose) for API
- Cookie-based session support for browser flows (secure, HttpOnly flags recommended)
- Password hashing with `passlib[bcrypt]`
- Pydantic models for request validation
- Environment-managed secrets (never checked into repo)

### 5) Rate-limiting & API rotation
- `APIRotator` utility rounds between configured API keys for providers with free tiers (AlphaVantage, etc.).
- Implement throttling at client-side and server-side to remain within free-tier limits.

## Frontend: pages list & core behaviors

- `index.html` — Landing; animated hero (particles.js), quick links to demo and signup.
- `about.html` — Illustrations, demos, and live-sim canvas (now wired to cached API poll on About page).
- `enhanced_research.html` — The main visual analytics page. Features:
   - Candlestick chart (Plotly)
   - Indicator overlays (SMA, Bollinger)
   - MACD and RSI subplots
   - Indicator toggles and MA-window inputs
   - Export chart as PNG via Plotly.toImage
   - Persist zoom/pan in `localStorage` under `zoom_<SYMBOL>`
- `research.html` — Basic research search UI
- `dashboard.html` — User dashboards and portfolio cards

Client patterns:
- Lightweight vanilla JS + Plotly for charts
- Progressive enhancement — server renders base HTML and JS augments interactions
- Local storage for UI state persistence

## Detailed architecture flow (ASCII)

```
User Browser
   |-- GET / (index.html)
   |-- GET /about
   |-- POST /api/research/enhanced -> FastAPI
                                        |
                                        +--> stock_service (data aggregation, indicators)
                                        |      +-> yfinance / AlphaVantage / IndStock
                                        +--> research_report_service (LLM orchestration)
                                        +--> pdf_generator (ReportLab)
                                        +-> returns JSON / PDF
```

## How to run (Windows recommended steps)

1) Create virtualenv

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

2) Install dependencies

```cmd
pip install -r requirements.txt
```

3) Set required environment variables (example)

```cmd
set ALPHAVANTAGE_KEY_1=your_key_here
set ENHANCED_CACHE_TTL=60
set DATABASE_URL=
```

4) Run the app

```cmd
python -m uvicorn app.main:app --reload --port 8000
```

5) (Optional) Install Playwright and capture screenshots

```cmd
pip install playwright
playwright install chromium
python tools\screenshot_capture.py
```

## Sample API usage

Quick enhanced research (curl):

```bash
curl -X POST "http://127.0.0.1:8000/api/research/enhanced" -H "Content-Type: application/json" -d '{"symbol":"AAPL","period":"1mo"}'
```

Expected partial payload:

```json
{
   "symbol": "AAPL",
   "chart_series": [{"date":"2025-10-01","close":150.52}, ...],
   "ohlc": [{"date":"2025-10-01","open":148.3,"high":151.4,"low":147.9,"close":150.52,"volume":23400000}, ...],
   "indicators": {"sma_20": {...}, "sma_50": {...}, "rsi_14": {...}},
   "macd": {"2025-09-30":0.12, ...}
}
```

## Recommended next steps / improvements

- Replace in-memory cache with Redis for multi-worker deployments
- Add unit tests for `stock_service` (happy-path + edge cases) and `pdf_generator`
- Add integration tests using Playwright to automatically capture screenshots and test UI flows
- Add role-based feature toggles and per-user preferences persisted in DB
