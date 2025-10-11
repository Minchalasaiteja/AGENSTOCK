from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List
import secrets
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson import ObjectId

from app.config import settings
from app.models.user import UserResponse, UserUpdate
from app.services.auth import get_current_active_user
from app.utils.security import get_db, get_password_hash

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def convert_objectid(obj):
    if isinstance(obj, list):
        return [convert_objectid(x) for x in obj]
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, ObjectId):
                obj[k] = str(v)
            else:
                obj[k] = convert_objectid(v)
    return obj

@router.get("/profile", response_class=HTMLResponse)
async def user_profile_page(request: Request, current_user: dict = Depends(get_current_active_user)):
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": current_user
    })

@router.put("/profile")
async def update_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    update_data = {}
    
    if user_update.email and user_update.email != current_user["email"]:
        # Generate verification code
        verification_code = secrets.token_hex(3).upper()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        # Store verification code
        db.email_verifications.update_one(
            {"email": user_update.email},
            {
                "$set": {
                    "code": verification_code,
                    "expires_at": expires_at,
                    "user_id": str(current_user["_id"])
                }
            },
            upsert=True
        )
        
        # Send verification email (you would implement this)
        # await send_verification_email(user_update.email, verification_code)
        
        update_data["email"] = user_update.email
        update_data["email_verified"] = False
    
    if user_update.full_name:
        update_data["full_name"] = user_update.full_name
    
    if user_update.password:
        update_data["hashed_password"] = get_password_hash(user_update.password)
    
    if update_data:
        db.users.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
    
    return {"message": "Profile updated successfully"}

@router.post("/verify-email")
async def verify_email(
    verification_data: dict,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    code = verification_data.get("code")
    email = verification_data.get("email")
    
    verification = db.email_verifications.find_one({
        "email": email,
        "code": code,
        "user_id": str(current_user["_id"])
    })
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    if verification["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired"
        )
    
    # Update user email verification status
    db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"email_verified": True}}
    )
    
    # Remove verification code
    db.email_verifications.delete_one({"_id": verification["_id"]})
    
    return {"message": "Email verified successfully"}


@router.post("/send-verification")
async def send_verification(request_data: dict, current_user: dict = Depends(get_current_active_user), db = Depends(get_db)):
    """Endpoint to (re)send a verification code to the user's email."""
    from datetime import datetime, timedelta
    import secrets
    email = request_data.get('email') or current_user.get('email')
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    # Generate code and store
    verification_code = secrets.token_hex(3).upper()
    expires_at = datetime.utcnow() + timedelta(hours=24)

    db.email_verifications.update_one(
        {"email": email},
        {"$set": {"code": verification_code, "expires_at": expires_at, "user_id": str(current_user["_id"]) }},
        upsert=True
    )

    # Send the email via service
    send_ok = False
    send_error = None
    try:
        from app.services.email_service import send_verification_email
        await send_verification_email(email, verification_code)
        send_ok = True
    except Exception as e:
        send_error = str(e)
        print('Failed to send verification email:', e)

    if send_ok:
        return {"message": "We sent a verification code to your email. Enter it below to verify your account."}
    else:
        # Return 202 so frontend can still show a retry option but not treat as fatal
        return {"message": "Failed to send verification email. Please try again later.", "error": send_error}

@router.get("/dashboard-data")
async def get_dashboard_data(
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_db)
):
    # Get user's portfolio summary
    portfolio = db.portfolios.find_one({"user_id": str(current_user["_id"])})
    
    # Get recent chat sessions
    recent_chats = list(db.chat_sessions.find(
        {"user_id": str(current_user["_id"]) }
    ).sort("updated_at", -1).limit(5))

    # Normalize recent_chats to ensure session_id and message_count are present
    for s in recent_chats:
        s["_id"] = str(s.get("_id"))
        s["session_id"] = str(s.get("session_id") or s.get("_id"))
        s["message_count"] = int(s.get("message_count") or 0)
        if isinstance(s.get("updated_at"), datetime):
            s["updated_at"] = s["updated_at"].isoformat()
    
    # Get watchlist
    watchlist = list(db.watchlists.find(
        {"user_id": str(current_user["_id"])}
    ))
    
    return {
        "portfolio_summary": {
            "total_value": portfolio.get("total_value", 0) if portfolio else 0,
            "daily_change": portfolio.get("daily_change", 0) if portfolio else 0,
            "total_pnl": portfolio.get("total_pnl", 0) if portfolio else 0
        },
        "recent_chats": convert_objectid(recent_chats),
        "watchlist": convert_objectid(watchlist),
        # Add realtime counts for profile/account stats
        "counts": {
            "chat_sessions": db.chat_sessions.count_documents({"user_id": str(current_user["_id"])}) if (db is not None and current_user) else 0,
            "research_reports": db.research_sessions.count_documents({"user_id": str(current_user["_id"])}) if (db is not None and current_user) else 0
        }
    }