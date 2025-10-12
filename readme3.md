<p align="center">
  <img width="450" height="450" alt="AGENSTOCK LOGo" src="https://github.com/user-attachments/assets/b7848135-e549-4d88-bc10-6c40ac686ca8" />
</p>


# AGENSTOCK - AI Stock Research Agent

<div align="center">

![AGENSTOCK](https://github.com/user-attachments/assets/e377513f-dcd3-456d-b5ca-21b12c7139ee)

<h3>Conversational AI-Driven Stock Research Platform</h3>

<p>
  <strong>Version 1.0.0</strong> | 
  <em>Multi-source data aggregation • Interactive analytics • PDF reports</em>
</p>

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)

</div>

## 🚀 Introduction

AGENSTOCK is a cutting-edge conversational AI-driven stock research application built with **FastAPI** and **Jinja2 templates**. It aggregates market and fundamental data, computes technical indicators, synthesizes insights with LLMs, and produces interactive charts with printable PDF research reports.

<div align="center">

### ✨ Key Features

</div>

<div class="features-grid">

<div class="feature-card">
<h4>🤖 Conversational AI Research Agent</h4>
<ul>
<li>Ask about any stock or portfolio in natural language</li>
<li>Receive multi-level summaries, investment theses, and risk annotations</li>
<li>Intelligent insights powered by advanced language models</li>
</ul>
</div>

<div class="feature-card">
<h4>📊 Enhanced Research Reports</h4>
<ul>
<li>Multi-source data synthesis with narrative explanations</li>
<li>Downloadable PDF reports with embedded high-resolution charts</li>
<li>Professional formatting with captions and bookmarks</li>
</ul>
</div>

<div class="feature-card">
<h4>📈 Interactive Visual Analytics</h4>
<ul>
<li>Candlestick charts with SMA, RSI, MACD, Bollinger Bands overlays</li>
<li>Toggle indicators on/off with zoom/pan state persistence</li>
<li>Export charts as PNG with one click</li>
</ul>
</div>

<div class="feature-card">
<h4>💼 Portfolio Tracking & Insights</h4>
<ul>
<li>Manage holdings and view allocation breakdown</li>
<li>AI-powered rebalancing suggestions</li>
<li>Performance tracking and analytics</li>
</ul>
</div>

<div class="feature-card">
<h4>⚖️ Stock Comparison</h4>
<ul>
<li>Compare multiple tickers side-by-side</li>
<li>Aggregated metrics and sentiment analysis</li>
<li>Visual comparison tools</li>
</ul>
</div>

<div class="feature-card">
<h4>🔒 Privacy-first Design</h4>
<ul>
<li>Focus on user data protection</li>
<li>Built with principle of least privilege</li>
<li>Secure authentication and session management</li>
</ul>
</div>

</div>

---

## 🛠️ Technical Overview

## 🏗️ System Architecture

<div align="center">

```mermaid
graph TD
    A[User Browser] --> B[FastAPI Backend]
    B --> C[Stock Service]
    B --> D[Research Report Service]
    C --> E[External APIs]
    C --> F[Data Processing]
    D --> G[LLM Integration]
    B --> H[PDF Generator]
    C --> I[Cache Layer]
    H --> J[ReportLab]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
```

</div>

---

<div class="tech-stack">

### 🏗️ Architecture & Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend Framework** | FastAPI (Python 3.10+) |
| **Frontend Templating** | Jinja2 |
| **Charting** | Plotly.js (client-side), mplfinance/matplotlib (server-side) |
| **PDF Generation** | ReportLab |
| **Data Processing** | pandas, numpy |
| **Data Providers** | yfinance, AlphaVantage, IndStock (IN market) |
| **Authentication** | JWT, OAuth2 |

</div>

### 📁 Project Structure

```
app/
├── templates/          # Jinja2 templates (html)
├── static/
│   ├── css/           # Stylesheets
│   └── js/            # Client-side scripts
├── models/             # Pydantic models
├── routes/             # FastAPI routers (api & pages)
├── services/           # Business logic and external API integration
├── utils/              # Helpers (pdf generator, security, rotating api keys)
└── main.py             # FastAPI app entrypoint

docs/
├── diagrams/
└── screenshots/

tools/
└── screenshot_capture.py
```

### 📋 Core Files Overview

| File | Purpose | Key Components |
|------|---------|----------------|
| `app/main.py` | Application entry point | Route mounting, app initialization |
| `app/routes/research.py` | Research endpoints | Enhanced research, PDF report generation |
| `app/services/stock_service.py` | Data aggregation & indicators | Historical data, technical indicators, caching |
| `app/utils/pdf_generator.py` | PDF composition | ReportLab integration, image embedding |
| `app/templates/enhanced_research.html` | Analytics UI | Plotly charts, export controls |

---

## 🎯 Core Features Deep Dive

### 1. Data Aggregation & Indicators
- **Multi-source data fetching** from yfinance, AlphaVantage, and IndStock
- **Technical indicators** including SMA, RSI, MACD, Bollinger Bands
- **Normalized data schema** for consistent processing

### 2. Enhanced Research & Caching
- **TTL-based caching** for expensive research payloads
- **Concurrent request protection** with async locks
- **LLM-powered insights** with structured output parsing

### 3. Interactive Visualization
- **Client-side Plotly.js** for responsive charts
- **State persistence** in localStorage for zoom/pan
- **Export functionality** to PNG format

### 4. PDF Report Generation
- **Professional layout** with two-column chart sections
- **High-resolution images** embedded for print quality
- **Bookmarks and TOC** for easy navigation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Virtual environment tool (venv, conda)

### Installation & Setup

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
set ALPHAVANTAGE_KEY_1=your_key_here
set ENHANCED_CACHE_TTL=60

# 5. Run the application
python -m uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000` to access the application.

### Sample API Usage

```bash
# Enhanced research endpoint
curl -X POST "http://127.0.0.1:8000/api/research/enhanced" \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","period":"1mo"}'
```

**Expected Response:**
```json
{
  "symbol": "AAPL",
  "chart_series": [{"date":"2025-10-01","close":150.52}, ...],
  "ohlc": [{"date":"2025-10-01","open":148.3,"high":151.4,"low":147.9,"close":150.52,"volume":23400000}, ...],
  "indicators": {"sma_20": {...}, "sma_50": {...}, "rsi_14": {...}},
  "macd": {"2025-09-30":0.12, ...}
}
```

---

## 🏗️ System Architecture

<div align="center">

```mermaid
graph TD
    A[User Browser] --> B[FastAPI Backend]
    B --> C[Stock Service]
    B --> D[Research Report Service]
    C --> E[External APIs]
    C --> F[Data Processing]
    D --> G[LLM Integration]
    B --> H[PDF Generator]
    C --> I[Cache Layer]
    H --> J[ReportLab]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
```

</div>

---

## 🔧 Development

### Running Tests
```bash
# Install test dependencies
pip install pytest playwright

# Run unit tests
pytest

# Capture screenshots (optional)
playwright install chromium
python tools\screenshot_capture.py
```

### Code Exploration
```bash
# List service functions
rg "def " app/services | sed -n '1,200p'
```

---

## 📈 Production Deployment

### Recommended Setup
- **Process Manager**: Gunicorn + Uvicorn workers
- **Cache**: Redis (replace in-memory cache)
- **Security**: HTTPS, secure cookies, environment secrets
- **Monitoring**: API rate limits, background tasks

### Environment Configuration
```bash
# Production environment variables
ALPHAVANTAGE_KEY_1=your_production_key
ENHANCED_CACHE_TTL=300
DATABASE_URL=postgresql://user:pass@host/db
REDIS_URL=redis://localhost:6379
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **PDF generation fails** | Install mplfinance and matplotlib |
| **Charts not rendering** | Check Plotly CDN access or serve locally |
| **Data fetch errors** | Verify API keys and rate limits |
| **Cache issues** | Restart application to clear in-memory cache |

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

---

## 📄 License
MIT License

Copyright (c) 2025 Minchala saiteja

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

<div align="center">

**AGENSTOCK** - *Intelligent Stock Research Made Accessible*

[Report Issue](https://github.com/your-repo/issues) • 
[Request Feature](https://github.com/your-repo/issues) • 
[Documentation](https://github.com/your-repo/docs)

</div>

<style>
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 1.5rem;
  margin: 2rem 0;
}

.feature-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 10px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-card h4 {
  margin-top: 0;
  border-bottom: 2px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 0.5rem;
}

.feature-card ul {
  padding-left: 1.2rem;
}

.feature-card li {
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.tech-stack table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
}

.tech-stack th, .tech-stack td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #ddd;
}

.tech-stack th {
  background-color: #f8f9fa;
  font-weight: 600;
}

.tech-stack tr:hover {
  background-color: #f5f5f5;
}

/* Responsive design */
@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .tech-stack table {
    font-size: 0.9rem;
  }
}

/* Code block styling */
pre {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 1rem;
  overflow-x: auto;
  margin: 1rem 0;
}

code {
  background: #f1f3f4;
  padding: 0.2rem 0.4rem;
  border-radius: 3px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9em;
}

/* Header styling */
h1, h2, h3 {
  color: #2c3e50;
  margin-top: 2rem;
}

h1 {
  border-bottom: 3px solid #3498db;
  padding-bottom: 0.5rem;
}

/* Link styling */
a {
  color: #3498db;
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}
</style>
