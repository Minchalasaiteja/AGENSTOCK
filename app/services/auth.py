from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from pymongo import MongoClient
import os
from dotenv import load_dotenv

from app.config import settings
from app.models.user import TokenData
from app.utils.security import get_db, verify_password, get_password_hash

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

async def authenticate_user(db: MongoClient, username: str, password: str):
    user = db.users.find_one({"username": username})
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(request: Request, db: MongoClient = Depends(get_db)):
    """Extract JWT from Authorization header (Bearer ...) or from cookie named access_token.
    This allows the frontend to send the token either as an Authorization header (used by
    SPA fetch calls with token in localStorage) or rely on the httponly cookie set on login.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = None
    # 1) Try Authorization header first
    auth_header = request.headers.get('Authorization')
    if auth_header:
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            token = parts[1]

    # 2) Fallback to cookie (legacy behavior)
    if not token:
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            token = cookie_token[7:] if cookie_token.startswith("Bearer ") else cookie_token
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception
    user = db.users.find_one({"username": token_data.username})
    if user is None:
        raise credentials_exception
    db.users.update_one(
        {"username": token_data.username},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    return user

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def require_admin(current_user: dict = Depends(get_current_active_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user