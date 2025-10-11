from typing import Dict, Any, Optional
import json
import re
from app.services.llm_service import llm_service
from app.services.stock_service import StockDataService
from app.services.stock_service import get_enhanced_research
from app.models.chat import ResearchResponse, RecommendationType, ConfidenceLevel, TargetPrice, InvestmentRecommendation, MultiLevelOutput
from app.config import settings
from app.services.mcp_service import MCPService
from datetime import datetime

class ResearchReportService:
    def __init__(self):
        self.stock_service = StockDataService()
        self.llm_service = llm_service
        self.mcp_service = MCPService(api_key=settings.alpha_vantage_keys[0])

    async def __aenter__(self):
        await self.stock_service.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stock_service.__aexit__(exc_type, exc_val, exc_tb)

    async def generate_full_research_report(self, symbol: str, query: str, timeframe: str) -> ResearchResponse:
        """
        Orchestrates the generation of a full, structured research report by fetching
        all necessary data and building a comprehensive context for the LLM.
        """
        # Fetch data from various sources
        quote = await self.stock_service.get_stock_quote(symbol)
        overview = await self.stock_service.get_company_overview(symbol)
        news = await self.stock_service.get_news_sentiment(symbol)
        # Enhanced payload for charts and indicators
        enhanced = await get_enhanced_research(symbol, period=timeframe)

        # Prepare context for LLM
        context_parts = [
            f"CURRENT PRICE: ${quote.get('05. price', 'N/A')}",
            f"COMPANY: {overview.get('Name', 'N/A')}",
            f"SECTOR: {overview.get('Sector', 'N/A')}",
            f"DESCRIPTION: {overview.get('Description', 'No description available')}",
            f"MARKET CAP: {overview.get('MarketCapitalization', 'N/A')}",
            f"P/E RATIO: {overview.get('PERatio', overview.get('trailingPE', 'N/A'))}",
            f"RECENT NEWS: {json.dumps(news.get('feed', [])[:5] if news else [])}"
        ]
        context = f"STOCK: {symbol}\nUSER QUERY: {query}\nTIMEFRAME: {timeframe}\n" + "\n".join(context_parts)

        llm_json_response = await self.llm_service.get_llm_response(prompt=query, context=context)

        # Parse the simplified LLM response into the structured Pydantic model
        report_model = self._parse_llm_to_pydantic(llm_json_response, overview)

        # Generate charts (PNG bytes) using Plotly if chart_series present
        charts = []
        try:
            import plotly.graph_objects as go
            import plotly.io as pio
            if enhanced and enhanced.get('chart_series'):
                series = enhanced['chart_series']
                dates = [s['date'] for s in series]
                closes = [s['close'] for s in series]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=dates, y=closes, mode='lines', name='Close', line=dict(color='#3a86ff')))
                # Add SMA overlays if available
                inds = enhanced.get('indicators', {})
                if inds.get('sma_20'):
                    sma20 = [inds['sma_20'].get(d) for d in dates]
                    fig.add_trace(go.Scatter(x=dates, y=sma20, mode='lines', name='SMA20', line=dict(dash='dash', color='#ff6363')))
                if inds.get('sma_50'):
                    sma50 = [inds['sma_50'].get(d) for d in dates]
                    fig.add_trace(go.Scatter(x=dates, y=sma50, mode='lines', name='SMA50', line=dict(dash='dot', color='#ffa600')))
                fig.update_layout(title=f'{symbol} Price', xaxis_title='Date', yaxis_title='Price')
                png_bytes = pio.to_image(fig, format='png', width=1200, height=600, scale=2)
                charts.append(png_bytes)
        except Exception as e:
            print(f"Chart generation failed: {e}")

        return { 'report': report_model, 'charts': charts, 'enhanced': enhanced }

    def _parse_llm_to_pydantic(self, llm_response: Dict[str, str], overview: Dict) -> ResearchResponse:
        """
        Parses the flat JSON from the LLM into the nested ResearchResponse Pydantic model.
        This adds a robust layer of processing to prevent validation errors.
        """
        
        # Helper to safely extract recommendation details
        def parse_recommendation(text: str) -> Optional[InvestmentRecommendation]:
            try:
                rec_text = text.lower()
                rec_type = RecommendationType.BUY if "buy" in rec_text else RecommendationType.HOLD if "hold" in rec_text else RecommendationType.SELL if "sell" in rec_text else RecommendationType.HOLD
                confidence = ConfidenceLevel.HIGH if "high" in rec_text else ConfidenceLevel.MEDIUM if "medium" in rec_text else ConfidenceLevel.LOW if "low" in rec_text else ConfidenceLevel.MEDIUM
                
                target_price_match = re.search(r"\$?(\d+\.?\d*)", text)
                target_price = float(target_price_match.group(1)) if target_price_match else 0.0
                
                return InvestmentRecommendation(
                    recommendation=rec_type,
                    target_price=TargetPrice(price=target_price, upside_percentage=0, calculation_method="LLM Analysis", assumptions={}, price_range={}),
                    confidence=confidence,
                    justification=text,
                    time_horizon="12 months",
                    key_catalysts=[]
                )
            except Exception:
                return None

        recommendation_text = llm_response.get("investment_recommendation", "")
        summary_text = llm_response.get("executive_summary", "No summary available.")
        deep_dive_text = llm_response.get("deep_dive_analysis", "No analysis available.")

        # Construct the multi-level output from the main text blocks
        multi_level_output = MultiLevelOutput(
            level1_tldr=summary_text.split('.')[0] + '.' if '.' in summary_text else summary_text,
            level2_highlights={
                "financial_highlights": [f"P/E Ratio: {overview.get('PERatio', 'N/A')}", f"Market Cap: {overview.get('MarketCapitalization', 'N/A')}"],
                "qualitative_highlights": [f"Sector: {overview.get('Sector', 'N/A')}", f"Industry: {overview.get('Industry', 'N/A')}"]
            },
            level3_deep_dive=deep_dive_text,
            level4_visuals_appendices={"summary": "Visual charts are generated separately based on fetched financial data."}
        )

        return ResearchResponse(
            summary=summary_text,
            deep_dive=deep_dive_text,
            metrics={
                "pe_ratio": f'{float(overview.get("PERatio", 0)):.2f}' if overview.get("PERatio") else "N/A",
                "eps": f'{float(overview.get("EPS", 0)):.2f}' if overview.get("EPS") else "N/A",
                "market_cap": f'${float(overview.get("MarketCapitalization", 0)) / 1e9:.2f}B' if overview.get("MarketCapitalization") else "N/A",
                "dividend_yield": f'{float(overview.get("DividendYield", 0)) * 100:.2f}%' if overview.get("DividendYield") else "N/A",
            },
            # Pass through the text blocks for the frontend to render
            growth_potential={"raw_text": llm_response.get("growth_potential")},
            peer_comparison={"raw_text": llm_response.get("peer_comparison")},
            risks={"raw_text": llm_response.get("risk_assessment")},
            cot_trace_tree={"raw_text": "CoT is implicitly used in the generation of each section."},
            # Populate the structured multi-level output
            multi_level_output=multi_level_output,
            recommendation=parse_recommendation(recommendation_text),
            generated_at=datetime.utcnow()
        )