import aiohttp
import asyncio
from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime, timedelta
import json

from app.config import settings
from app.utils.api_rotator import APIRotator
from math import isnan
import numpy as np


# Simple in-memory TTL cache for enhanced research payloads
_enhanced_cache: Dict[str, Dict] = {}
_enhanced_locks: Dict[str, asyncio.Lock] = {}
_CACHE_TTL_DEFAULT = getattr(settings, 'ENHANCED_CACHE_TTL', 60)


def detect_market(symbol: str) -> str:
    """
    Detect market by symbol format. Returns 'IN' for Indian stocks, 'US' for US stocks, else 'GLOBAL'.
    """
    symbol = symbol.upper()
    if symbol.endswith('.NS') or symbol.endswith('.BO') or symbol.startswith('NSE:') or symbol.startswith('BSE:'):
        return 'IN'
    # Add more rules for other markets as needed
    return 'US' if symbol.isalpha() and len(symbol) <= 5 else 'GLOBAL'

class StockDataService:

    async def get_yf_sentiment(self, symbol: str) -> Dict:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        news = ticker.news if hasattr(ticker, 'news') else []
        # Simple sentiment: count positive/negative words in headlines
        from textblob import TextBlob
        sentiments = []
        for item in news:
            headline = item.get('title', '')
            blob = TextBlob(headline)
            sentiments.append(blob.sentiment.polarity)
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
        return {
            'symbol': symbol,
            'news_count': len(news),
            'avg_sentiment': avg_sentiment,
            'news': news
        }
    def __init__(self):
        self.alpha_vantage_rotator = APIRotator(settings.alpha_vantage_keys)
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def get_stock_quote(self, symbol: str) -> Dict:
        """Get real-time stock quote, using IndStock for IN, yfinance for GLOBAL, AlphaVantage for US."""
        market = detect_market(symbol)
        # Normalize symbol for yfinance for Indian stocks
        yf_symbol = symbol
        if market == 'IN' and not symbol.upper().endswith('.NS') and not symbol.upper().endswith('.BO'):
            # allow users to pass NSE:RELIANCE or RELIANCE -> convert to RELIANCE.NS
            yf_symbol = symbol.replace('NSE:', '').replace('BSE:', '') + '.NS'
        else:
            yf_symbol = symbol
        if market == 'IN':
            # Prefer yfinance for IN (supports .NS/.BO). Fall back to nsetools/nsepython/indstock when available.
            try:
                import yfinance as yf
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                return {
                    'Symbol': yf_symbol,
                    'Price': info.get('regularMarketPrice'),
                    'MarketCap': info.get('marketCap'),
                    'PERatio': info.get('trailingPE'),
                    'EPS': info.get('trailingEps'),
                    'DividendYield': info.get('dividendYield'),
                }
            except Exception as e:
                print(f"yfinance (IN) quote failed: {e}")
            # nsetools
            try:
                import importlib
                nsetools_mod = importlib.import_module('nsetools')
                Nse = getattr(nsetools_mod, 'Nse')
                nse = Nse()
                qsym = yf_symbol.replace('.NS', '').lower()
                quote = nse.get_quote(qsym)
                return {
                    'Symbol': symbol,
                    'Price': quote.get('lastPrice'),
                    'MarketCap': quote.get('marketCap'),
                }
            except Exception as e:
                print(f"nsetools quote failed: {e}")
            try:
                import importlib
                nsepython_mod = importlib.import_module('nsepython')
                nse_eq = getattr(nsepython_mod, 'nse_eq')
                clean = yf_symbol.replace('.NS', '')
                q = nse_eq(clean)
                return q or {}
            except Exception as e:
                print(f"nsepython quote failed: {e}")
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'Symbol': symbol,
                'Price': info.get('regularMarketPrice'),
                'MarketCap': info.get('marketCap'),
                'PERatio': info.get('trailingPE'),
                'EPS': info.get('trailingEps'),
                'DividendYield': info.get('dividendYield'),
            }
        except Exception as e:
            print(f"yfinance quote failed: {e}")
        # Fallback to AlphaVantage for US stocks
        api_key = self.alpha_vantage_rotator.get_next_key()
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}"
        async with self.session.get(url) as response:
            data = await response.json()
            return data.get("Global Quote", {})
    
    async def get_company_overview(self, symbol: str) -> Dict:
        """Get company overview and fundamentals, using IndStock for IN, yfinance for GLOBAL, AlphaVantage for US."""
        market = detect_market(symbol)
        yf_symbol = symbol
        if market == 'IN' and not symbol.upper().endswith('.NS') and not symbol.upper().endswith('.BO'):
            yf_symbol = symbol.replace('NSE:', '').replace('BSE:', '') + '.NS'
        if market == 'IN':
            try:
                import yfinance as yf
                ticker = yf.Ticker(yf_symbol)
                info = ticker.info
                return {
                    'Symbol': yf_symbol,
                    'Name': info.get('shortName'),
                    'Description': info.get('longBusinessSummary'),
                    'Sector': info.get('sector'),
                    'Industry': info.get('industry'),
                    'MarketCapitalization': info.get('marketCap'),
                    'PERatio': info.get('trailingPE'),
                    'EPS': info.get('trailingEps'),
                    'DividendYield': info.get('dividendYield'),
                    '52WeekHigh': info.get('fiftyTwoWeekHigh'),
                    '52WeekLow': info.get('fiftyTwoWeekLow'),
                }
            except Exception as e:
                print(f"yfinance (IN) overview failed: {e}")
            try:
                import importlib
                nsepython_mod = importlib.import_module('nsepython')
                nse_quote = getattr(nsepython_mod, 'nse_quote')
                clean = yf_symbol.replace('.NS', '')
                q = nse_quote(clean)
                return q or {}
            except Exception as e:
                print(f"nsepython overview failed: {e}")
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return {
                'Symbol': symbol,
                'Name': info.get('shortName'),
                'Description': info.get('longBusinessSummary'),
                'Sector': info.get('sector'),
                'Industry': info.get('industry'),
                'MarketCapitalization': info.get('marketCap'),
                'PERatio': info.get('trailingPE'),
                'EPS': info.get('trailingEps'),
                'DividendYield': info.get('dividendYield'),
                '52WeekHigh': info.get('fiftyTwoWeekHigh'),
                '52WeekLow': info.get('fiftyTwoWeekLow'),
            }
        except Exception as e:
            print(f"yfinance failed for overview, falling back to AlphaVantage. Error: {e}")
        api_key = self.alpha_vantage_rotator.get_next_key()
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={api_key}"
        async with self.session.get(url) as response:
            return await response.json()
    
    async def get_historical_data(self, symbol: str, period: str = "1month") -> pd.DataFrame:
        """Get historical price data, using IndStock for IN, yfinance for GLOBAL, AlphaVantage for US."""
        market = detect_market(symbol)
        if market == 'IN':
            try:
                from indstocks import IndStock
                ind = IndStock()
                clean_symbol = symbol.replace('NSE:', '').replace('BSE:', '').replace('.NS', '').replace('.BO', '')
                df = ind.get_historical_data(clean_symbol, period=period)
                return df
            except Exception as e:
                print(f"IndStock historical failed: {e}")
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)
            return hist
        except Exception as e:
            print(f"yfinance historical failed: {e}")
        api_key = self.alpha_vantage_rotator.get_next_key()
        function = "TIME_SERIES_DAILY"
        if period == "1year":
            function = "TIME_SERIES_WEEKLY"
        url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={api_key}&outputsize=compact"
        async with self.session.get(url) as response:
            data = await response.json()
            time_series = data.get("Time Series (Daily)", data.get("Weekly Time Series", {}))
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df = df.astype(float)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            return df
    
    async def get_news_sentiment(self, symbol: str) -> Dict:
        """Get news sentiment for stock"""
        api_key = self.alpha_vantage_rotator.get_next_key()
        url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={api_key}"
        
        async with self.session.get(url) as response:
            return await response.json()
    
    async def get_technical_indicators(self, symbol: str, indicator: str = "SMA") -> Dict:
        """Get technical indicators"""
        api_key = self.alpha_vantage_rotator.get_next_key()
        url = f"https://www.alphavantage.co/query?function={indicator}&symbol={symbol}&interval=daily&time_period=10&series_type=close&apikey={api_key}"
        
        async with self.session.get(url) as response:
            return await response.json()

stock_service = StockDataService()


def _sma(series: pd.Series, window: int = 14) -> pd.Series:
    return series.rolling(window=window).mean()


def _rsi(series: pd.Series, window: int = 14) -> pd.Series:
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(com=window - 1, adjust=False).mean()
    ma_down = down.ewm(com=window - 1, adjust=False).mean()
    rs = ma_up / ma_down
    rsi = 100 - (100 / (1 + rs))
    return rsi


async def get_enhanced_research(symbol: str, period: str = "1mo") -> Dict:
    """Compose an enhanced research payload combining overview, quote, historical series, indicators, and sentiment.

    Returns a dict suitable for rendering in Enhanced Research UI or for PDF report generation.
    """
    svc = stock_service
    result: Dict = {'symbol': symbol}
    # Cache key uses normalized symbol + period
    key = f"{symbol.upper()}|{period}"
    now = datetime.utcnow()
    ttl = getattr(settings, 'ENHANCED_CACHE_TTL', _CACHE_TTL_DEFAULT)
    # Return cached result if available and fresh
    cached = _enhanced_cache.get(key)
    if cached and (now - cached['ts']).total_seconds() < ttl:
        return cached['data']

    # Acquire per-key lock to avoid duplicate parallel fetches
    lock = _enhanced_locks.get(key)
    if not lock:
        lock = asyncio.Lock()
        _enhanced_locks[key] = lock

    async with lock:
        # Re-check cache inside lock
        cached = _enhanced_cache.get(key)
        if cached and (datetime.utcnow() - cached['ts']).total_seconds() < ttl:
            return cached['data']
    market = detect_market(symbol)
    yf_symbol = symbol
    if market == 'IN' and not symbol.upper().endswith('.NS') and not symbol.upper().endswith('.BO'):
        yf_symbol = symbol.replace('NSE:', '').replace('BSE:', '') + '.NS'
    # Overview
    try:
        overview = await svc.get_company_overview(symbol)
        result['overview'] = overview
    except Exception as e:
        result['overview_error'] = str(e)
    # Quote
    try:
        quote = await svc.get_stock_quote(symbol)
        result['quote'] = quote
    except Exception as e:
        result['quote_error'] = str(e)
    # Historical
    try:
        hist = await svc.get_historical_data(symbol, period=period)
        # Ensure DataFrame index and close column
        if isinstance(hist, pd.DataFrame):
            close_col = None
            open_col = None
            high_col = None
            low_col = None
            vol_col = None
            for c in ['Close', 'close', 'Adj Close', 'adjclose', 'adj_close']:
                if c in hist.columns:
                    close_col = c
                    break
            # detect OHLC and volume columns
            for c in ['Open', 'open', '1. open']:
                if c in hist.columns:
                    open_col = c
                    break
            for c in ['High', 'high', '2. high']:
                if c in hist.columns:
                    high_col = c
                    break
            for c in ['Low', 'low', '3. low']:
                if c in hist.columns:
                    low_col = c
                    break
            for c in ['Volume', 'volume', '5. volume']:
                if c in hist.columns:
                    vol_col = c
                    break
            if close_col is None and len(hist.columns) >= 1:
                close_col = hist.columns[-1]
            close_series = hist[close_col].dropna()
            result['historical'] = hist.to_dict(orient='index')
            # Indicators
            result['indicators'] = {
                'sma_20': _sma(close_series, 20).dropna().tail(200).to_dict(),
                'sma_50': _sma(close_series, 50).dropna().tail(200).to_dict(),
                'rsi_14': _rsi(close_series, 14).dropna().tail(200).to_dict(),
            }
            # Chart-ready series (list of {date, close})
            series = [{'date': str(idx.date()), 'close': float(v)} for idx, v in close_series.items()]
            result['chart_series'] = series[-365:]
            # Build OHLC series if available (for candlestick)
            try:
                ohlc = []
                for idx, row in hist.iterrows():
                    try:
                        d = str(pd.to_datetime(idx).date())
                        o = float(row[open_col]) if open_col and open_col in row.index else float(row[close_col])
                        h = float(row[high_col]) if high_col and high_col in row.index else o
                        l = float(row[low_col]) if low_col and low_col in row.index else o
                        cval = float(row[close_col])
                        vol = int(row[vol_col]) if vol_col and vol_col in row.index and not pd.isna(row[vol_col]) else 0
                        ohlc.append({'date': d, 'open': o, 'high': h, 'low': l, 'close': cval, 'volume': vol})
                    except Exception:
                        continue
                result['ohlc'] = ohlc[-365:]
                # Compute MACD (12/26/9) and attach as date->value maps
                try:
                    close_float = pd.to_numeric(close_series, errors='coerce')
                    exp1 = close_float.ewm(span=12, adjust=False).mean()
                    exp2 = close_float.ewm(span=26, adjust=False).mean()
                    macd = exp1 - exp2
                    signal = macd.ewm(span=9, adjust=False).mean()
                    macd_map = {str(idx.date()): float(v) for idx, v in macd.dropna().items()}
                    signal_map = {str(idx.date()): float(v) for idx, v in signal.dropna().items()}
                    result['macd'] = macd_map
                    result['macd_signal'] = signal_map
                except Exception:
                    pass
            except Exception:
                pass
        else:
            result['historical_error'] = 'historical data not a DataFrame'
    except Exception as e:
        result['historical_error'] = str(e)
    # Sentiment using yfinance/news where available
    try:
        try:
            sentiment = await svc.get_yf_sentiment(symbol if detect_market(symbol) != 'IN' else yf_symbol)
        except Exception:
            sentiment = await svc.get_yf_sentiment(symbol)
        result['sentiment'] = sentiment
    except Exception as e:
        result['sentiment_error'] = str(e)
    # store result in cache before returning
    try:
        _enhanced_cache[key] = {'ts': datetime.utcnow(), 'data': result}
    except Exception:
        # best effort caching
        pass

    return result