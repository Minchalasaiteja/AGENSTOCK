from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    mongodb_url: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017/")
    database_name: str = os.getenv("DATABASE_NAME", "stock_research")
    
    # JWT
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Admin
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@agenstock.com")
    
    # API Keys with rotation
    gemini_api_keys: List[str] = [
        os.getenv("GEMINI_API_KEY_1", ""),
        os.getenv("GEMINI_API_KEY_2", ""),
        os.getenv("GEMINI_API_KEY_3", ""),
        os.getenv("GEMINI_API_KEY_4", "")
    ]
    
    alpha_vantage_keys: List[str] = [
        os.getenv("ALPHA_VANTAGE_KEY_1", ""),
        os.getenv("ALPHA_VANTAGE_KEY_2", ""),
        os.getenv("ALPHA_VANTAGE_KEY_3", ""),
        os.getenv("ALPHA_VANTAGE_KEY_4", "")
    ]
    
    # Other APIs
    finhub_api_key: str = os.getenv("FINHUB_API_KEY", "")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    market_aux_api_key: str = os.getenv("MARKET_AUX_API_KEY", "")
    polygon_api_key: str = os.getenv("POLYGON_API_KEY", "")
    fmp_api_key: str = os.getenv("FMP_API_KEY", "")
    
    # Pinecone
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-west1-gcp")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "stock-research")
    
    # Email
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    email_username: str = os.getenv("EMAIL_USERNAME", "")
    email_password: str = os.getenv("EMAIL_PASSWORD", "")

settings = Settings()