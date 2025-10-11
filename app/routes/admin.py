from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any
from datetime import datetime, timedelta
from pymongo import MongoClient
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

from app.config import settings
from app.models.user import UserRole, UserCreate
from app.services.auth import get_current_active_user, get_password_hash
from app.utils.security import get_db, require_admin
from app.services.auth import require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(
    request: Request,
    current_user: dict = Depends(require_admin)
):
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": current_user
    })

@router.get("/users", response_class=HTMLResponse)
async def admin_users_page(
    request: Request,
    current_user: dict = Depends(require_admin)
):
    return templates.TemplateResponse("admin/users.html", {
        "request": request,
        "user": current_user
    })

@router.get("/analytics", response_class=HTMLResponse)
async def admin_analytics_page(
    request: Request,
    current_user: dict = Depends(require_admin)
):
    return templates.TemplateResponse("admin/analytics.html", {
        "request": request,
        "user": current_user
    })

@router.get("/users/list")
async def get_users_list(
    request: Request,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    users = list(db.users.find(
        {"role": UserRole.USER},
        {"hashed_password": 0}
    ).sort("created_at", -1))
    result = []
    for idx, user in enumerate(users, start=1):
        result.append({
            "si_no": idx,
            "_id": str(user.get("_id", "")),
            "username": user.get("username", ""),
            "full_name": user.get("full_name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", ""),
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at").isoformat() if user.get("created_at") else None,
            "last_login": user.get("last_login").isoformat() if user.get("last_login") else None
        })
    return result

@router.post("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    from bson import ObjectId
    
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not user.get("is_active", True)
    db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_active": new_status}}
    )
    
    return {"message": f"User {'activated' if new_status else 'deactivated'} successfully"}

@router.post("/create-admin")
async def create_admin(
    admin_data: dict,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    # Allow any admin to create other admins (restriction removed)
    
    # Check if username exists
    if db.users.find_one({"username": admin_data["username"]}):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email exists
    if db.users.find_one({"email": admin_data["email"]}):
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new admin user
    hashed_password = get_password_hash(admin_data["password"])
    admin_user = {
        "username": admin_data["username"],
        "email": admin_data["email"],
        "hashed_password": hashed_password,
        "full_name": admin_data.get("full_name", ""),
        "role": UserRole.ADMIN,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "email_verified": True
    }
    
    db.users.insert_one(admin_user)
    
    return {"message": "Admin user created successfully"}

@router.get("/analytics/data")
async def get_analytics_data(
    request: Request,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    # User analytics
    total_users = db.users.count_documents({"role": UserRole.USER})
    active_users = db.users.count_documents({"role": UserRole.USER, "is_active": True})
    new_users_today = db.users.count_documents({
        "role": UserRole.USER,
        "created_at": {"$gte": datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)}
    })
    
    # Chat analytics
    total_chats = db.chat_sessions.count_documents({})
    total_messages = db.chat_messages.count_documents({})
    
    # Portfolio analytics
    total_portfolios = db.portfolios.count_documents({})
    
    # Daily active users (last 7 days)
    daily_active_data = []
    for i in range(7):
        date = datetime.utcnow() - timedelta(days=i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        daily_active = db.users.count_documents({
            "last_login": {"$gte": start_of_day, "$lte": end_of_day}
        })
        daily_active_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "active_users": daily_active
        })
    
    daily_active_data.reverse()
    
    # Chat activity by hour (example)
    chat_activity = []
    for hour in range(6, 22, 3):
        start = datetime.utcnow().replace(hour=hour, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=3)
        count = db.chat_messages.count_documents({
            "created_at": {"$gte": start, "$lt": end}
        })
        chat_activity.append({"hour": f"{hour}:00", "messages": count})

    # Feature usage (example: count by type)
    feature_usage = [
        {"label": "Research", "value": db.research.count_documents({}) if "research" in db.list_collection_names() else 0},
        {"label": "Portfolio", "value": db.portfolios.count_documents({}) if "portfolios" in db.list_collection_names() else 0},
        {"label": "Chat", "value": db.chat_sessions.count_documents({}) if "chat_sessions" in db.list_collection_names() else 0},
        {"label": "Comparison", "value": db.chat_sessions.count_documents({"type": "compare"}) if "chat_sessions" in db.list_collection_names() else 0}
    ]

    return {
        "user_metrics": {
            "total_users": total_users,
            "active_users": active_users,
            "new_users_today": new_users_today
        },
        "chat_metrics": {
            "total_chats": total_chats,
            "total_messages": total_messages,
            "chat_activity": chat_activity
        },
        "portfolio_metrics": {
            "total_portfolios": total_portfolios
        },
        "daily_active_users": daily_active_data,
        "feature_usage": feature_usage
    }

@router.get("/analytics/charts")
async def get_analytics_charts(
    request: Request,
    current_user: dict = Depends(require_admin),
    db = Depends(get_db)
):
    # Generate user registration trend chart
    dates = []
    registrations = []
    
    for i in range(30):
        date = datetime.utcnow() - timedelta(days=29-i)
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        count = db.users.count_documents({
            "created_at": {"$gte": start_of_day, "$lte": end_of_day}
        })
        
        dates.append(date.strftime("%m-%d"))
        registrations.append(count)
    
    # Create matplotlib figure
    plt.figure(figsize=(10, 6))
    plt.plot(dates, registrations, marker='o', linewidth=2, markersize=4)
    plt.title('User Registrations (Last 30 Days)')
    plt.xlabel('Date')
    plt.ylabel('Registrations')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Convert to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    
    return {
        "registration_chart": f"data:image/png;base64,{image_base64}"
    }


@router.get('/recent-activity')
async def get_recent_activity(
    current_user: dict = Depends(require_admin),
    db = Depends(get_db),
    limit: int = 20
):
    """Return recent system/user activity for admin dashboard.
    This will first try to read from an `activity_logs` collection. If that doesn't exist,
    it will fall back to recent chat sessions and portfolio updates to provide useful data.
    """
    activities = []
    # Try activity_logs collection
    try:
        if 'activity_logs' in db.list_collection_names():
            cursor = db.activity_logs.find().sort('timestamp', -1).limit(limit)
            for doc in cursor:
                activities.append({
                    'user': doc.get('username') or doc.get('user') or 'system',
                    'activity': doc.get('message') or doc.get('action') or 'action',
                    'time': doc.get('timestamp').isoformat() if doc.get('timestamp') else None,
                    'status': doc.get('status', 'info')
                })
            return activities
    except Exception:
        # If any error, continue to fallback
        pass

    # Fallback: recent chat sessions
    try:
        chats = list(db.chat_sessions.find().sort('created_at', -1).limit(limit))
        for c in chats:
            activities.append({
                'user': c.get('username') or c.get('user') or 'unknown',
                'activity': f"Chat session started ({c.get('messages', 0)} msgs)",
                'time': c.get('created_at').isoformat() if c.get('created_at') else None,
                'status': 'success'
            })
    except Exception:
        pass

    # Fallback: recent portfolio updates
    try:
        ports = list(db.portfolios.find().sort('updated_at', -1).limit(limit))
        for p in ports:
            activities.append({
                'user': p.get('username') or p.get('owner') or 'unknown',
                'activity': 'Portfolio updated',
                'time': p.get('updated_at').isoformat() if p.get('updated_at') else None,
                'status': 'info'
            })
    except Exception:
        pass

    # Trim to requested limit
    return activities[:limit]