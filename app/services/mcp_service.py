import requests
from typing import Dict, Any

class MCPService:
    def __init__(self, api_key: str):
        self.base_url = f"https://mcp.alphavantage.co/mcp?apikey={api_key}"

    def get_financials(self, symbol: str) -> Dict[str, Any]:
        url = f"{self.base_url}&function=FINANCIALS&symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_company_info(self, symbol: str) -> Dict[str, Any]:
        url = f"{self.base_url}&function=COMPANY_OVERVIEW&symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def get_news(self, symbol: str) -> Dict[str, Any]:
        url = f"{self.base_url}&function=NEWS_SENTIMENT&symbol={symbol}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
