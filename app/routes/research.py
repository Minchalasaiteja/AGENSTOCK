from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Dict, Any, List
from datetime import datetime
import json

router = APIRouter()

@router.get("/categories")
async def get_available_categories():
    """Return available data source/tool categories for research."""
    categories = [
        {
            "id": "financials",
            "name": "Financial Data",
            "description": "Company financials, ratios, time series from MCP/AlphaVantage."
        },
        {
            "id": "company",
            "name": "Company Info",
            "description": "Company overview, sector, industry, management."
        },
        {
            "id": "news",
            "name": "News & Sentiment",
            "description": "Recent news, sentiment analysis, qualitative signals."
        },
        {
            "id": "charts",
            "name": "Charts & Visuals",
            "description": "Price trends, volume, comparative charts."
        },
        {
            "id": "risk",
            "name": "Risk Assessment",
            "description": "Market, company, and sector risk analysis."
        }
    ]
    return {"categories": categories}
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Dict, Any, List
from datetime import datetime
import json

router = APIRouter()

@router.get("/history")
async def get_research_history(user_id: str, query: str = None, top_k: int = 5):
    """Retrieve historical research sessions using vector DB similarity search."""
    from app.services.vector_db import VectorDBService
    import numpy as np
    vector_db = VectorDBService()
    # Simulate embedding for query (replace with actual embedding from LLM)
    embedding = np.random.rand(768).tolist() if query else None
    if embedding:
        results = vector_db.query_research(embedding, top_k=top_k)
        return {"results": results}
    else:
        return {"results": []}
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from typing import Dict, Any, List
from datetime import datetime
import json

from app.config import settings
from app.services.auth import get_current_active_user
from app.services.llm_service import llm_service
from app.services.stock_service import StockDataService
from app.services.research_report_service import ResearchReportService
from app.services.stock_service import get_enhanced_research
from app.utils.pdf_generator import PDFReportGenerator
from app.utils.security import get_db

router = APIRouter()
pdf_generator = PDFReportGenerator()

@router.post("/stock")
async def research_stock(
    research_data: dict,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    symbol = research_data.get("symbol", "").upper()
    query = research_data.get("query", "")
    timeframe = research_data.get("timeframe", "1y")
    categories = research_data.get("categories", [])

    if not symbol or not query:
        raise HTTPException(status_code=400, detail="Symbol and query are required")

    async with StockDataService() as stock_service:
        try:
            # Get comprehensive stock data
            quote = await stock_service.get_stock_quote(symbol) if not categories or "financials" in categories else {}
            overview = await stock_service.get_company_overview(symbol) if not categories or "company" in categories else {}
            historical_data = await stock_service.get_historical_data(symbol, timeframe) if not categories or "charts" in categories else None
            news = await stock_service.get_news_sentiment(symbol) if not categories or "news" in categories else None
            # Fallbacks for missing data
            mcp_context_parts = []
            if (not quote or not overview or (historical_data is not None and historical_data.empty)):
                # Try MCP as fallback
                try:
                    from app.services.mcp_service import MCPService
                    mcp = MCPService(api_key=settings.alpha_vantage_keys[0])
                    mcp_financials = mcp.get_financials(symbol) if not categories or "financials" in categories else {}
                    mcp_company = mcp.get_company_info(symbol) if not categories or "company" in categories else {}
                    mcp_news = mcp.get_news(symbol) if not categories or "news" in categories else None
                    # Merge MCP data if available
                    if mcp_financials:
                        quote.update(mcp_financials)
                        mcp_context_parts.append(f"MCP FINANCIALS: {mcp_financials}")
                    if mcp_company:
                        overview.update(mcp_company)
                        mcp_context_parts.append(f"MCP COMPANY INFO: {mcp_company}")
                    if mcp_news:
                        news = mcp_news
                        mcp_context_parts.append(f"MCP NEWS: {mcp_news}")
                except Exception as mcp_err:
                    print(f"MCP fallback failed: {mcp_err}")
            
            mcp_context = "\n".join(mcp_context_parts)
            # Prepare context for LLM
            context_parts = []
            if not categories or "financials" in categories:
                context_parts.append(f"CURRENT PRICE: ${quote.get('05. price', 'N/A')}")
            if not categories or "company" in categories:
                context_parts.append(f"COMPANY: {overview.get('Name', 'N/A')}")
                context_parts.append(f"SECTOR: {overview.get('Sector', 'N/A')}")
                context_parts.append(f"INDUSTRY: {overview.get('Industry', 'N/A')}")
                context_parts.append(f"DESCRIPTION: {overview.get('Description', 'No description available')}")
            if not categories or "financials" in categories:
                context_parts.append(f"MARKET CAP: {overview.get('MarketCapitalization', 'N/A')}")
                context_parts.append(f"P/E RATIO: {overview.get('PERatio', 'N/A')}")
                context_parts.append(f"EPS: {overview.get('EPS', 'N/A')}")
                context_parts.append(f"DIVIDEND YIELD: {overview.get('DividendYield', 'N/A')}")
                context_parts.append(f"52W HIGH: {overview.get('52WeekHigh', 'N/A')}")
                context_parts.append(f"52W LOW: {overview.get('52WeekLow', 'N/A')}")
            if not categories or "news" in categories:
                context_parts.append(f"RECENT NEWS: {json.dumps(news.get('feed', [])[:5] if news else [])}")
            context_parts.append(f"USER QUERY: {query}")
            context = f"STOCK: {symbol}\n" + "\n".join(context_parts) + f"\n{mcp_context}"
            # Get AI analysis
            try:
                analysis = await llm_service.get_llm_response(query, context)
            except Exception as llm_err:
                raise HTTPException(status_code=500, detail=f"Research failed: {llm_err}")

            # Parse the analysis into structured format (llm_service returns dict on success)
            structured_analysis = analysis if isinstance(analysis, dict) else {"raw": str(analysis)}
            # Save research session
            research_session = {
                "user_id": str(current_user["_id"]),
                "symbol": symbol,
                "query": query,
                "analysis": structured_analysis,
                "generated_at": datetime.utcnow(),
                "timeframe": timeframe,
                "categories": categories
            }
            db.research_sessions.insert_one(research_session)
            # Store embedding in vector DB for long-term memory
            try:
                import numpy as np
                from app.services.vector_db import vector_db
                # Use LLMService to get embedding (simulate with hash for demo)
                embedding = np.random.rand(768).tolist()  # Replace with actual embedding from LLM if available
                vector_db.upsert_research(str(research_session["user_id"]) + "_" + symbol + "_" + str(research_session["generated_at"]), embedding, research_session)
            except Exception as vdb_err:
                print(f"Vector DB upsert failed: {vdb_err}")
            return structured_analysis

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")

@router.post("/compare")
async def compare_stocks(
    comparison_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    symbols = comparison_data.get("symbols", [])
    metrics = comparison_data.get("metrics", [])

    if len(symbols) < 2:
        raise HTTPException(status_code=400, detail="At least two symbols required")

    if len(symbols) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 symbols allowed")

    try:
        # Use yfinance for real data with rate limiting
        import yfinance as yf
        from textblob import TextBlob
        import time
        comparison_result = []
        metric_set = set(metrics) if metrics else {"price", "market_cap", "pe_ratio", "eps", "dividend_yield"}
        # Gather data for each symbol
        symbol_data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                # Add delay between API calls to avoid rate limiting
                time.sleep(1)
                info = ticker.info
                symbol_data[symbol] = {
                    "price": info.get("regularMarketPrice"),
                    "market_cap": info.get("marketCap"),
                    "pe_ratio": info.get("trailingPE"),
                    "eps": info.get("trailingEps"),
                    "dividend_yield": info.get("dividendYield"),
                }
                # Sentiment analysis
                news = ticker.news[:3] if hasattr(ticker, 'news') and ticker.news else []
                sentiments = []
                for item in news:
                    headline = item.get('title', '')
                    blob = TextBlob(headline)
                    sentiments.append(blob.sentiment.polarity)
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
                symbol_data[symbol]["sentiment"] = avg_sentiment
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                symbol_data[symbol] = {
                    "price": None,
                    "market_cap": None,
                    "pe_ratio": None,
                    "eps": None,
                    "dividend_yield": None,
                    "sentiment": 0
                }
        # Build comparison table
        for metric in metric_set:
            row = {"metric": metric}
            for symbol in symbols:
                row[symbol] = symbol_data[symbol].get(metric)
            comparison_result.append(row)
        # Add sentiment row
        sentiment_row = {"metric": "sentiment"}
        for symbol in symbols:
            sentiment_row[symbol] = symbol_data[symbol]["sentiment"]
        comparison_result.append(sentiment_row)
        return {
            "symbols": symbols,
            "comparison": comparison_result,
            "generated_at": datetime.utcnow()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")

@router.post("/sentiment")
async def analyze_sentiment(
    sentiment_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    symbol = sentiment_data.get("symbol", "").upper()
    news_articles = sentiment_data.get("articles", [])
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    # If no articles provided, fetch recent news
    if not news_articles:
        async with StockDataService() as stock_service:
            news_data = await stock_service.get_news_sentiment(symbol)
            news_articles = [item.get('title', '') for item in news_data.get('feed', [])[:10]]
    
    try:
        sentiment_analysis = await llm_service.sentiment_analysis(news_articles, symbol)
        
        return {
            "symbol": symbol,
            "sentiment_analysis": sentiment_analysis,
            "articles_analyzed": len(news_articles),
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentiment analysis failed: {str(e)}")

@router.post("/generate-report")
async def generate_research_report(
    report_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    symbol = report_data.get("symbol", "").upper()
    analysis_data = report_data.get("analysis", {})
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    # Get additional stock data for the report
    async with StockDataService() as stock_service:
        quote = await stock_service.get_stock_quote(symbol)
        overview = await stock_service.get_company_overview(symbol)
        historical_data = await stock_service.get_historical_data(symbol, "1y")
        stock_data = {
            "symbol": symbol,
            "price": quote.get('05. price', 'N/A'),
            "company_name": overview.get('Name', 'N/A'),
            "sector": overview.get('Sector', 'N/A'),
            "market_cap": overview.get('MarketCapitalization', 'N/A')
        }
    # Generate chart image from historical data
    chart_img = None
    try:
        import matplotlib.pyplot as plt
        import io
        plt.figure(figsize=(6, 2))
        plt.plot(historical_data.index, historical_data['4. close'], label='Close Price')
        plt.title(f"{symbol} Price Trend (1Y)")
        plt.xlabel("Date")
        plt.ylabel("Price (USD)")
        plt.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        chart_img = buf.read()
        plt.close()
    except Exception as chart_err:
        chart_img = None
    charts = [chart_img] if chart_img else []
    # Generate PDF report
    pdf_bytes = pdf_generator.generate_stock_report(stock_data, analysis_data, charts)
    # Return PDF file
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=AGENSTOCK_Research_{symbol}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        }
    )

@router.post("/enhanced-report")
async def generate_enhanced_research_report(
    report_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    """Generate an enhanced research report with all required components"""
    symbol = report_data.get("symbol", "").upper()
    query = report_data.get("query", f"Provide a comprehensive investment analysis for {symbol}")
    timeframe = report_data.get("timeframe", "1y")
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Symbol is required")
    
    try:
        # Generate the enhanced research report using the new service
        async with ResearchReportService() as report_service:
            research_bundle = await report_service.generate_full_research_report(symbol, query, timeframe)
        report_model = research_bundle.get('report')
        charts = research_bundle.get('charts', [])
        return {
            "symbol": symbol,
            "research_report": report_model.dict() if hasattr(report_model, 'dict') else report_model,
            "charts_available": len(charts) > 0,
            "enhanced": research_bundle.get('enhanced'),
            "generated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research report generation failed: {str(e)}")


@router.post("/enhanced")
async def enhanced_research_ajax(
    request_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    """AJAX endpoint returning enhanced research payload for frontend rendering (lightweight)."""
    symbol = request_data.get('symbol', '').upper()
    timeframe = request_data.get('timeframe', '1y')
    if not symbol:
        raise HTTPException(status_code=400, detail='Symbol is required')
    try:
        payload = await get_enhanced_research(symbol, period=timeframe)
        return { 'symbol': symbol, 'research': payload, 'generated_at': datetime.utcnow() }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Enhanced research failed: {e}')


@router.post("/enhanced-public")
async def enhanced_research_public(request_data: dict):
    """Public demo endpoint for enhanced research. Returns a reduced payload and does not require authentication.

    This is intended for the demo/About/landing pages where we want to show the visualizations
    without requiring a user session. It intentionally avoids any database writes.
    """
    symbol = (request_data.get('symbol') or '').upper()
    timeframe = request_data.get('timeframe', '1y')
    if not symbol:
        raise HTTPException(status_code=400, detail='Symbol is required')
    try:
        # Import lazily to avoid circular imports at module import time
        payload = await get_enhanced_research(symbol, period=timeframe)
        # Reduce payload size for public demo: remove heavy fields if any
        demo_payload = {
            'overview': payload.get('overview') if payload else {},
            'quote': payload.get('quote') if payload else {},
            'chart_series': payload.get('historical') if payload else [],
            'indicators': payload.get('indicators') if payload else {}
        }
        return { 'symbol': symbol, 'research': demo_payload }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Public enhanced research failed: {e}')

@router.post("/enhanced-report-pdf")
async def generate_enhanced_research_report_pdf(
    report_data: dict,
    current_user: dict = Depends(get_current_active_user)
):
    """Generate an enhanced research report as PDF"""
    symbol = report_data.get("symbol", "").upper()
    query = report_data.get("query", f"Provide a comprehensive investment analysis for {symbol}")
    timeframe = report_data.get("timeframe", "1y")
    
    if not symbol:
        raise HTTPException(status_code=400, detail="Stock symbol is required.")
    
    try:
        # Use the report service to get both the model and charts
        async with ResearchReportService() as report_service:
            research_bundle = await report_service.generate_full_research_report(symbol, query, timeframe)
        report_model = research_bundle.get('report')
        charts = research_bundle.get('charts', [])

        # Assemble data and generate the PDF using returned charts
        stock_data = {
            "symbol": symbol,
            "company_name": (report_model and getattr(report_model, 'summary', None)) or symbol,
        }
        pdf_bytes = pdf_generator.generate_enhanced_stock_report(
            stock_data=stock_data,
            analysis_data={},
            charts=charts,
            research_response=report_model
        )
        
        # Step 5: Return the final PDF
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=AGENSTOCK_Enhanced_Research_{symbol}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced research report generation failed: {str(e)}")