import google.generativeai as genai
from langchain_community.llms import GooglePalm
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
import asyncio
from typing import List, Dict
import time

from app.config import settings
import json
from app.utils.api_rotator import APIRotator
from app.services.mcp_service import MCPService

class LLMService:
    def __init__(self):
        self.gemini_rotator = APIRotator(settings.gemini_api_keys)
        self.current_key_index = 0
        self.mcp = MCPService(api_key=settings.alpha_vantage_keys[0])
        
    async def get_llm_response(self, prompt: str, context: str = "", conversation_history: List = None):
        """Get response from Gemini with API key rotation"""
        # The context is now fully prepared by the calling function.
        full_context = context
        for attempt in range(len(settings.gemini_api_keys)):
            try:
                api_key = self.gemini_rotator.get_next_key()
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                research_prompt = f"""You are an expert financial analyst generating a research report.

**CONTEXT:**
{full_context}

**USER QUERY:**
{prompt}

---
### **Instructions**

Your task is to generate a detailed financial analysis based on the provided context and user query. Use Chain-of-Thought (CoT) reasoning for each section.

**Output Format:**
Generate a response in a **single, valid JSON object** with the following keys. Each value should be a well-written text block in markdown format.

```json
{{
  "executive_summary": "A brief, one-paragraph summary of the investment thesis.",
  "deep_dive_analysis": "A detailed analysis combining quantitative (Data-CoT) and qualitative (Thesis-CoT) insights. Use markdown for tables and lists.",
  "key_metrics": "A markdown table of key metrics like P/E, EPS, Market Cap, and Dividend Yield.",
  "growth_potential": "Analysis of growth potential, including CAGR forecasts, revenue/EPS trends, and key drivers.",
  "peer_comparison": "A markdown table comparing the company to 2-3 peers on key metrics, followed by a brief analysis.",
  "risk_assessment": "A list of key risks (Regulatory, Competitive, Market) with probability/impact notes and mitigation insights (Risk-CoT).",
  "investment_recommendation": "A final recommendation (BUY/HOLD/SELL), a target price with justification, and a confidence level (Low/Medium/High)."
}}
```

**IMPORTANT:**
- The output **must be a single, valid JSON object and nothing else**.
- Do not wrap the JSON in markdown backticks.
- Derive all insights directly from the provided context.

---
**START JSON OUTPUT:**
"""
                # Some SDK versions do not accept GenerationConfig parameters; call generate_content directly
                response = await asyncio.to_thread(
                    model.generate_content,
                    research_prompt
                )
                # Extract and parse JSON from the model response defensively
                raw_text = getattr(response, 'text', '') or str(response)
                import re
                m = re.search(r"\{[\s\S]*\}", raw_text)
                json_text = m.group(0) if m else raw_text
                try:
                    return json.loads(json_text)
                except Exception:
                    try:
                        fixed = json_text.replace("'", '"')
                        return json.loads(fixed)
                    except Exception as e2:
                        raise Exception(f"LLM JSON parse error: {e2} | raw: {raw_text[:200]}")

            except Exception as e:
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    print(f"API key {api_key[:10]}... reached limit, rotating...")
                    self.gemini_rotator.report_error(api_key, e)
                    continue
                else:
                    raise e
        raise Exception("All API keys exhausted")

    async def get_streaming_llm_response(self, prompt: str, context: str = "", conversation_history: List = None):
        """Get a streaming response from Gemini with API key rotation."""
        full_context = context
        for attempt in range(len(settings.gemini_api_keys)):
            try:
                api_key = self.gemini_rotator.get_next_key()
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                chat_prompt = f"""You are a helpful financial AI assistant named AGENSTOCK.

**CONTEXT:**
{full_context}

**USER QUERY:**
{prompt}

---
**Instructions:**
- Provide a concise, helpful, and conversational response.
- If financial data is present, use it to inform your answer.
- Use markdown for formatting if it helps clarity (e.g., lists, bolding).
---
**RESPONSE:**
"""
                response_stream = await asyncio.to_thread(
                    model.generate_content,
                    chat_prompt,
                    stream=True
                )
                return response_stream
            except Exception as e:
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    print(f"API key {api_key[:10]}... reached limit, rotating...")
                    self.gemini_rotator.report_error(api_key, e)
                    continue
                else:
                    raise e
        raise Exception("All API keys exhausted")
    
    async def compare_stocks(self, stock_symbols: List[str], metrics: List[str] = None):
        """Compare multiple stocks"""
        if metrics is None:
            metrics = ["PE Ratio", "Market Cap", "Revenue Growth", "Profit Margin", "Dividend Yield"]
        
        comparison_prompt = f"""
        Compare the following stocks: {', '.join(stock_symbols)}
        Key metrics to analyze: {', '.join(metrics)}
        
        Provide a comparative analysis including:
        1. Relative valuation
        2. Growth prospects
        3. Risk profiles
        4. Investment recommendation ranking
        5. Sector comparison
        """
        
        return await self.get_llm_response(comparison_prompt)
    
    async def sentiment_analysis(self, news_articles: List[str], stock_symbol: str):
        """Perform sentiment analysis on news articles"""
        sentiment_prompt = f"""
        Analyze sentiment for {stock_symbol} based on these news articles:
        
        {chr(10).join(news_articles)}
        
        Provide:
        1. Overall sentiment score (Positive/Negative/Neutral)
        2. Key positive factors
        3. Key negative factors
        4. Impact assessment on stock price
        5. Confidence level in analysis
        """
        
        return await self.get_llm_response(sentiment_prompt)


llm_service = LLMService()