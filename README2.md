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
14. License

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

### How to add screenshots/diagrams to README
1. Create a `docs/screenshots/` folder in the repo.
2. Add the PNG images (landing, chart, pdf preview).
3. Use Markdown image references as shown earlier.

---

If you'd like, I can:
- Replace ASCII diagrams with generated SVG diagrams and save them under `docs/diagrams/`.
- Add concrete screenshots by taking snapshots of the running app (I can run a smoke test and capture visuals if you allow running the app here).

