<img width="1536" height="1024" alt="Agenstock" src="https://github.com/user-attachments/assets/e377513f-dcd3-456d-b5ca-21b12c7139ee" />






# AGENSTOCK 

Version: 1.0.0

## Introduction

AGENSTOCK is a conversational AI-driven stock research application built with FastAPI and Jinja2 templates. It aggregates market and fundamental data, computes technical indicators, synthesizes insights with LLMs, and produces interactive charts and printable PDF research reports.


# AGENSTOCK — AI Stock Research Agent

Key features (user-facing)

- Conversational AI Research Agent
  - Ask about any stock or portfolio in natural language.
  - Receive multi-level summaries, investment theses, and risk annotations.

- Enhanced Research Reports
  - Multi-source data synthesis, narrative explanations, and recommended actions.
  - Downloadable PDF reports with embedded high-resolution charts and captions.

- Interactive Visual Analytics
  - Candlestick charts, SMA (various windows), RSI, MACD, Bollinger Bands overlays.
  - Toggle indicators on/off, zoom/pan with state persistence, and export charts as PNG.

- Portfolio Tracking & Insights
  - Manage holdings, view allocation breakdown, and receive AI-powered rebalancing suggestions.

- Stock Comparison
  - Compare multiple tickers side-by-side with aggregated metrics and sentiment analysis.

- Privacy-first Design
  - Focus on user data protection; features built with the principle of least privilege for user data.


---





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

# AGENSTOCK — Comprehensive README

Version: 1.0.0

## Table of Contents

1. Project overview
2. Key features (user-facing only)
3. Architecture and components
4. Data sources and processing
5. Frontend details and UI behavior
6. Backend services and endpoints
7. PDF report generation
8. Caching and performance
9. Security and privacy considerations
10. Development setup and running locally
11. Production deployment notes
12. Troubleshooting and common issues
13. Contributing


---

## 1. Project overview

AGENSTOCK is a conversational AI-powered stock research platform that helps retail users explore, analyze, and generate high-quality research reports. The goal is to make multi-source financial analysis accessible via natural language interactions, accompanied by rich interactive visualizations and exportable research PDFs.

The platform is focused on user-facing features: research queries, enhanced research reports, portfolio tracking, and visual analytics. Admin or internal management features are intentionally excluded from this user-facing documentation.

## 2. Key features (user-facing)

- Conversational AI Research Agent
  - Ask about any stock or portfolio in natural language.
  - Receive multi-level summaries, investment theses, and risk annotations.

- Enhanced Research Reports
  - Multi-source data synthesis, narrative explanations, and recommended actions.
  - Downloadable PDF reports with embedded high-resolution charts and captions.

- Interactive Visual Analytics
  - Candlestick charts, SMA (various windows), RSI, MACD, Bollinger Bands overlays.
  - Toggle indicators on/off, zoom/pan with state persistence, and export charts as PNG.

- Portfolio Tracking & Insights
  - Manage holdings, view allocation breakdown, and receive AI-powered rebalancing suggestions.

- Stock Comparison
  - Compare multiple tickers side-by-side with aggregated metrics and sentiment analysis.

- Privacy-first Design
  - Focus on user data protection; features built with the principle of least privilege for user data.

## 3. Architecture and components

High-level components:

- Frontend: Jinja2 templates, static assets (CSS/JS). Interactive charts use Plotly.js on the client for dynamic visualization.
- Backend: FastAPI application providing REST endpoints for research, chat, portfolio, and PDF generation.
- Services: Modular Python services provide data aggregation (stock_service), LLM orchestration (research_report_service), email, and vector DB utilities.
- Data Layer: External data sources (yfinance, AlphaVantage, IndStock, and more). The system normalizes historical OHLC data for charts and indicators.
- PDF Generation: ReportLab is used to compose PDF research reports with server-generated chart images embedded for consistent prints.
- Caching: Lightweight in-memory TTL cache for expensive enhanced research payloads to reduce repeated costly fetches.

## 4. Data sources and processing

- Primary data providers:
  - yfinance (for global and many international tickers)
  - Alpha Vantage (fallback for quotes, Time Series data, and news sentiment)
  - IndStock / nsepython / nsetools for Indian market data where available

- Processing:
  - Historical OHLC data is normalized into a consistent schema (date, open, high, low, close, volume).
  - Technical indicators are computed server-side: SMA (windows 20/50 or configurable), RSI (14), MACD (12/26/9), Bollinger Bands.
  - Sentiment: news headlines are processed into simple polarity metrics (TextBlob used in some code paths).

## 5. Frontend details and UI behavior

- Landing Page: Static preview of features with animated hero and a link to "About" in the header.
- Enhanced Research UI: Uses client-side Plotly.js to render candlestick charts with overlays and subplots for MACD/RSI. UI controls allow toggling indicators and exporting PNGs. Zoom/pan is persisted locally.
- About Page: Provides a rich animated description of the product, live simulation canvas (visual-only), and explanation of how the app works.

Live animations are implemented using a lightweight canvas script that simulates a moving price line with area fill and subtle badges. These are purely visual and do not fetch live market data.

## 6. Backend services and endpoints

Key endpoints (users only):

- GET / — Landing page
- GET /about — About page (new)
- GET /research — Research landing
- GET /enhanced-research — Enhanced Research UI
- POST /api/research/enhanced — Quick payload for chart rendering (cached)
- POST /api/research/enhanced-report — Full research (LLM synthesis + charts)
- POST /api/research/enhanced-report-pdf — Generate and return PDF report

Other supporting endpoints:
- /chat, /chats, /portfolio, /profile
- Authentication endpoints under /api/auth for login/signup (OAuth2 password flow)

Services:
- stock_service.py: Aggregates quotes, historicals, indicators, and sentiment. Contains a TTL in-memory cache for enhanced research payloads.
- research_report_service.py: Orchestrates LLM calls and report generation; returns structured ResearchResponse and chart images.
- pdf_generator.py: Builds PDF reports with high-resolution images, captions, and bookmarks.

## 7. PDF report generation

- Implemented with ReportLab for programmatic PDF layout.
- Charts are generated server-side (Plotly or mplfinance/matplotlib) and embedded as PNG images into a two-column layout with captions and a basic table-of-contents with bookmarks.
- Images are saved at a higher DPI where possible for crisp printing.

## 8. Caching and performance

- The `get_enhanced_research` function uses a per-process in-memory TTL cache to avoid repeated heavy data fetches and LLM calls.
- TTL defaults to 60 seconds but can be configured via `ENHANCED_CACHE_TTL` in settings.
- For production/scale, it's recommended to replace the in-memory cache with Redis or another shared cache when running multiple workers.

## 9. Security and privacy considerations

- Authentication: OAuth2-like password flow and token cookies are used for session management.
- Access controls: The About page intentionally exposes only user-facing features; admin pages are available under /admin and are not mentioned here.
- Secrets: API keys (AlphaVantage, etc.) are loaded from environment variables and should be stored securely.

## 10. Development setup and running locally

Prerequisites:
- Python 3.10+ (3.11 recommended)
- virtualenv or conda

Install dependencies (example using pip):

```
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Run the application:

```
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 in your browser. The About page is available at `/about`.

Notes:
- Optional packages (mplfinance, plotly) are used for server-side chart generation; missing libs will result in graceful fallbacks for the UI (client-side Plotly remains available via CDN).
- If using AlphaVantage, set API keys in environment: `ALPHAVANTAGE_KEY_1`, `ALPHAVANTAGE_KEY_2`, ... or set `ALPHA_VANTAGE_KEYS` list in config.

## 11. Production deployment notes

- Use a process manager (gunicorn + uvicorn workers) or containerization (Docker) for deployment.
- Replace the in-memory cache with Redis to share cached enhanced payloads across workers.
- Configure HTTPS and secure cookies for auth tokens.
- Monitor background tasks and rate limits for external APIs.

## 12. Troubleshooting and common issues

- PDF generation fails with server 500:
  - Ensure optional dependencies mplfinance and matplotlib are installed.
  - Check logs for tracebacks in `pdf_generator.py`.

- Charts not rendering:
  - Ensure client can load Plotly CDN (network access) or install plotly locally and serve it from static when offline.

- Data fetch errors:
  - Rate limits from AlphaVantage or other providers; consider API key rotation or paid tiers.

## 13. Contributing

- Fork the repo, create a feature branch, and submit pull requests.
- Run tests (add unit tests for services and endpoints) and follow code style.

## 14. License

- Add your license here (MIT recommended for open source).

---

For questions or help setting up the project, open an issue or contact the maintainers.

## Appendix: Screenshots, Diagrams and Examples

### Screenshot placeholders
Below are recommended screenshots to include in the final README repository (place files under `docs/screenshots/` and update paths):

- `docs/screenshots/landing.png` — Landing hero and features
- `docs/screenshots/enhanced_research_chart.png` — Enhanced Research chart with overlays
- `docs/screenshots/report_preview.png` — Generated PDF preview (two-column charts)

Example Markdown embed:

```
![Landing](/docs/screenshots/landing.png)
![Enhanced Chart](/docs/screenshots/enhanced_research_chart.png)
![PDF Preview](/docs/screenshots/report_preview.png)
```

### Detailed architecture diagram (ASCII)
This is a more detailed representation you can convert into a diagram using any tool.

```
                           +------------------------+
                           |   User Browser (UI)    |
                           | - Jinja2 templates     |
                           | - Plotly.js (client)   |
                           +----------+-------------+
                                      |
                                      | AJAX / REST
                                      |
                    +-----------------v------------------+
                    |             FastAPI App            |
                    |  - Routes: /api/research/*          |
                    |  - Services orchestrator            |
                    +--+-----------------+----------------+
                       |                 |
         +-------------v--+           +--v--------------+
         | stock_service   |           | research_report |
         | - yfinance      |           | _service (LLM)  |
         | - AlphaVantage  |           | - LLM prompt    |
         | - IndStock/etc  |           +-----------------+
         +-----------------+
                       |
                       | indicator calc, normalizing
                       v
                 +-----+------+    (cache TTL)
                 |  Cache     | <---------------+
                 +------------+                 |
                       |                        |
                       v                        |
                  PDF generator                  |
                  (reportlab + images)          |
                       |                        |
                       +------------------------+
```

### Environment and configuration examples
Set environment variables (example for Windows `cmd.exe`):

```
set ALPHAVANTAGE_KEY_1=your_key_here
set ALPHAVANTAGE_KEY_2=your_key_here
set ENHANCED_CACHE_TTL=60
set DATABASE_URL=sqlite:///./data.db
```

For a `.env` file (used by `python-dotenv`):

```
ALPHAVANTAGE_KEY_1=your_key_here
ALPHAVANTAGE_KEY_2=your_key_here
ENHANCED_CACHE_TTL=60
DATABASE_URL=sqlite:///./data.db
```

### Sample API usage and payloads

Quick enhanced research (client example using fetch):

```js
const res = await fetch('/api/research/enhanced', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ symbol: 'AAPL', period: '1mo' }) });
const payload = await res.json();
console.log(payload.chart_series.slice(-5));
```

Example partial enhanced payload shape (trimmed):

```json
{
  "symbol": "AAPL",
  "chart_series": [{"date":"2025-10-01","close":150.52}, ...],
  "ohlc": [{"date":"2025-10-01","open":148.3,"high":151.4,"low":147.9,"close":150.52,"volume":23400000}, ...],
  "indicators": {"sma_20": {...}, "sma_50": {...}, "rsi_14": {...}},
  "macd": {"2025-09-30":0.12, ...}
}
```

### Sample LLM prompt snippet (how research_report_service frames prompts)

```
You are an investment research assistant. Given the following data: historical OHLC, indicators, and company overview. Produce a concise executive summary, an investment thesis, risk factors, and recommended next steps.
```



---


