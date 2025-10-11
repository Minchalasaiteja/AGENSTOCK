from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
from pymongo import MongoClient

from app.config import settings
from app.services.auth import get_current_active_user
from app.services.stock_service import StockDataService
from app.utils.security import get_db
import json
from app.routes.chat import manager as chat_manager

router = APIRouter()

@router.get("/")
async def get_user_portfolio(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    portfolio = db.portfolios.find_one({"user_id": current_user["_id"]})
    
    if not portfolio:
        # Create default portfolio if doesn't exist
        portfolio = {
            "user_id": current_user["_id"],
            "name": "My Portfolio",
            "description": "Default investment portfolio",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "total_value": 0,
            "cash_balance": 0,
            "holdings": []
        }
        result = db.portfolios.insert_one(portfolio)
        portfolio["_id"] = str(result.inserted_id)
    else:
        portfolio["_id"] = str(portfolio["_id"])
    
    return portfolio

@router.get("/holdings")
async def get_portfolio_holdings(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    portfolio = db.portfolios.find_one({"user_id": current_user["_id"]})
    
    if not portfolio:
        return []
    
    # Update current prices
    async with StockDataService() as stock_service:
        updated_holdings = []
        total_value = 0
        
        for holding in portfolio.get("holdings", []):
            symbol = holding["symbol"]
            quote = await stock_service.get_stock_quote(symbol)
            current_price = float(quote.get('05. price', holding.get('current_price', 0)))
            
            updated_holding = {
                **holding,
                "current_price": current_price,
                "total_value": holding["quantity"] * current_price,
                "unrealized_pnl": (current_price - holding["average_cost"]) * holding["quantity"],
                "unrealized_pnl_percent": ((current_price - holding["average_cost"]) / holding["average_cost"]) * 100
            }
            
            updated_holdings.append(updated_holding)
            total_value += updated_holding["total_value"]
        
        # Update portfolio total value
        db.portfolios.update_one(
            {"user_id": current_user["_id"]},
            {
                "$set": {
                    "holdings": updated_holdings,
                    "total_value": total_value + portfolio.get("cash_balance", 0),
                    "updated_at": datetime.utcnow()
                }
            }
        )

        # Broadcast portfolio update to connected clients
        try:
            portfolio_summary = db.portfolios.find_one({"user_id": current_user["_id"]})
            if portfolio_summary:
                portfolio_summary["_id"] = str(portfolio_summary["_id"])
                await chat_manager.broadcast(json.dumps({"type": "portfolio_update", "portfolio": {
                    "total_value": portfolio_summary.get("total_value"),
                    "cash_balance": portfolio_summary.get("cash_balance", 0)
                }}))
        except Exception:
            pass
    
    return updated_holdings

@router.post("/holdings")
async def add_holding(
    holding_data: dict,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    symbol = holding_data.get("symbol", "").upper()
    quantity = float(holding_data.get("quantity", 0))
    price = float(holding_data.get("price", 0))
    
    if quantity <= 0 or price <= 0:
        raise HTTPException(status_code=400, detail="Invalid quantity or price")
    
    # Get current stock price for validation
    async with StockDataService() as stock_service:
        quote = await stock_service.get_stock_quote(symbol)
        if not quote or '05. price' not in quote:
            raise HTTPException(status_code=400, detail="Invalid stock symbol")
    
    portfolio = db.portfolios.find_one({"user_id": current_user["_id"]})
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if holding already exists
    existing_holding = None
    for holding in portfolio.get("holdings", []):
        if holding["symbol"] == symbol:
            existing_holding = holding
            break
    
    if existing_holding:
        # Update existing holding (average cost)
        total_quantity = existing_holding["quantity"] + quantity
        total_cost = (existing_holding["quantity"] * existing_holding["average_cost"]) + (quantity * price)
        average_cost = total_cost / total_quantity
        
        db.portfolios.update_one(
            {"user_id": current_user["_id"], "holdings.symbol": symbol},
            {
                "$set": {
                    "holdings.$.quantity": total_quantity,
                    "holdings.$.average_cost": average_cost,
                    "holdings.$.current_price": price,
                    "updated_at": datetime.utcnow()
                }
            }
        )
    else:
        # Add new holding
        new_holding = {
            "symbol": symbol,
            "quantity": quantity,
            "average_cost": price,
            "current_price": price,
            "total_value": quantity * price,
            "added_at": datetime.utcnow()
        }
        
        db.portfolios.update_one(
            {"user_id": current_user["_id"]},
            {
                "$push": {"holdings": new_holding},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
    
    # Add transaction record
    transaction = {
        "portfolio_id": str(portfolio["_id"]),
        "symbol": symbol,
        "type": "buy",
        "quantity": quantity,
        "price": price,
        "total_amount": quantity * price,
        "fee": 0.0,
        "timestamp": datetime.utcnow(),
        "notes": holding_data.get("notes", "")
    }
    
    db.transactions.insert_one(transaction)

    # Broadcast portfolio change event
    try:
        portfolio_summary = db.portfolios.find_one({"user_id": current_user["_id"]})
        if portfolio_summary:
            await chat_manager.broadcast(json.dumps({"type": "portfolio_update", "portfolio": {
                "total_value": portfolio_summary.get("total_value"),
                "cash_balance": portfolio_summary.get("cash_balance", 0)
            }}))
    except Exception:
        pass
    
    return {"message": "Holding added successfully"}

@router.delete("/holdings/{symbol}")
async def remove_holding(
    symbol: str,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    portfolio = db.portfolios.find_one({"user_id": current_user["_id"]})
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Remove holding
    db.portfolios.update_one(
        {"user_id": current_user["_id"]},
        {
            "$pull": {"holdings": {"symbol": symbol.upper()}},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Holding removed successfully"}

@router.get("/analysis")
async def get_portfolio_analysis(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    portfolio = db.portfolios.find_one({"user_id": current_user["_id"]})
    
    if not portfolio:
        return {
            "total_value": 0,
            "total_invested": 0,
            "total_pnl": 0,
            "total_pnl_percent": 0,
            "diversification": {},
            "risk_metrics": {},
            "performance_metrics": {}
        }
    
    # Calculate portfolio metrics
    total_invested = 0
    total_value = portfolio.get("cash_balance", 0)
    sector_allocation = {}
    
    for holding in portfolio.get("holdings", []):
        invested = holding["quantity"] * holding["average_cost"]
        current_value = holding["quantity"] * holding.get("current_price", holding["average_cost"])
        
        total_invested += invested
        total_value += current_value
        
        # Simple sector allocation (would need actual sector data)
        sector = "Technology"  # This should come from stock data
        sector_allocation[sector] = sector_allocation.get(sector, 0) + current_value
    
    total_pnl = total_value - total_invested
    total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    
    # Normalize sector allocation to percentages
    for sector in sector_allocation:
        sector_allocation[sector] = (sector_allocation[sector] / total_value) * 100
    
    analysis = {
        "total_value": total_value,
        "total_invested": total_invested,
        "total_pnl": total_pnl,
        "total_pnl_percent": total_pnl_percent,
        "daily_change": 0,  # Would need historical data
        "daily_change_percent": 0,
        "diversification": sector_allocation,
        "risk_metrics": {
            "volatility": "Medium",  # Simplified
            "beta": 1.0,
            "sharpe_ratio": 0.0
        },
        "performance_metrics": {
            "ytd_return": 0.0,
            "annualized_return": 0.0
        }
    }
    
    return analysis