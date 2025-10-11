from pymongo import MongoClient
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from datetime import datetime
from app.config import settings

# Create password context here to avoid circular imports
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_db():
    from pymongo import MongoClient
    client = MongoClient(settings.mongodb_url)
    db = client[settings.database_name]
    try:
        yield db
    finally:
        client.close()

async def create_default_admin():
    """Create default admin user if not exists"""
    client = MongoClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    admin_user = db.users.find_one({"username": settings.admin_username})
    
    if not admin_user:
        hashed_password = get_password_hash(settings.admin_password)
        admin_user = {
            "username": settings.admin_username,
            "email": settings.admin_email,
            "hashed_password": hashed_password,
            "full_name": "System Administrator",
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "email_verified": True
        }
        
        db.users.insert_one(admin_user)
        print("Default admin user created")
    
    client.close()

async def require_admin(current_user: dict):
    """Dependency to require admin role"""
    from app.services.auth import get_current_active_user
    current_user = await get_current_active_user(current_user)
    
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user