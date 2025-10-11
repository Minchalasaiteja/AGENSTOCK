from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class Portfolio(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    total_value: float
    cash_balance: float

class PortfolioHolding(BaseModel):
    id: str
    portfolio_id: str
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    total_value: float
    unrealized_pnl: float
    unrealized_pnl_percent: float

class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"

class Transaction(BaseModel):
    id: str
    portfolio_id: str
    symbol: str
    type: TransactionType
    quantity: float
    price: float
    total_amount: float
    fee: float = 0.0
    timestamp: datetime
    notes: Optional[str] = None

class PortfolioAnalysis(BaseModel):
    portfolio_id: str
    total_value: float
    total_invested: float
    total_pnl: float
    total_pnl_percent: float
    daily_change: float
    daily_change_percent: float
    diversification: Dict[str, float]  # sector allocation
    risk_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]