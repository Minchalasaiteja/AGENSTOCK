from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
router = APIRouter()
# Logout route
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Logged out"}
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta, datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

from app.config import settings
from app.models.user import UserInDB, Token
from app.services.auth import (
    authenticate_user, 
    create_access_token, 
    get_current_active_user,
    get_current_user
)
from app.utils.security import get_db, get_password_hash

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db = Depends(get_db)
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, 
        expires_delta=access_token_expires
    )
    
    # Set cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        expires=1800,
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signup")
async def signup(user_data: dict, db = Depends(get_db)):
    # Check if user exists
    if db.users.find_one({"username": user_data["username"]}):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.users.find_one({"email": user_data["email"]}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data["password"])
    user = {
        "username": user_data["username"],
        "email": user_data["email"],
        "hashed_password": hashed_password,
        "full_name": user_data.get("full_name", ""),
        "role": "user",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "email_verified": False
    }
    
    result = db.users.insert_one(user)
    user["_id"] = str(result.inserted_id)
    
    return {"message": "User created successfully", "user_id": user["_id"]}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}

@router.get("/me")
async def read_users_me(current_user: dict = Depends(get_current_active_user)):
    return {
        "username": current_user["username"],
        "email": current_user["email"],
        "full_name": current_user.get("full_name", ""),
        "role": current_user["role"],
        "is_active": current_user["is_active"],
        "created_at": current_user["created_at"],
        "last_login": current_user.get("last_login"),
        "email_verified": current_user.get("email_verified", False)
    }