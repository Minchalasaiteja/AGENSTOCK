from fastapi import FastAPI, Request, Depends, HTTPException
from app.services.auth import get_current_user
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.config import Settings
from app.routes import auth, users, admin, chat, portfolio, research
from app.utils.security import create_default_admin

load_dotenv()

app = FastAPI(
    title="AGENSTOCK - AI Stock Research Agent",
    description="Conversational Stock Research Platform",
    version="1.0.0",
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": "your-client-id" # Placeholder
    }
)


# Attach OpenAPI security definitions so the Swagger UI shows an Authorize button
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = app.openapi()
    openapi_schema.setdefault('components', {})
    openapi_schema['components'].setdefault('securitySchemes', {})
    openapi_schema['components']['securitySchemes']['OAuth2Password'] = {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/api/auth/token",
                "scopes": {}
            }
        }
    }
    # Do not force global security; endpoints can opt-in. This makes the Authorize button available.
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define security scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["portfolio"])
app.include_router(research.router, prefix="/api/research", tags=["research"])


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, user: dict = Depends(get_current_user, use_cache=False)):
    return templates.TemplateResponse("chat.html", {"request": request, "user": user})


@app.get("/chats", response_class=HTMLResponse)
async def chats_page(request: Request, user: dict = Depends(get_current_user, use_cache=False)):
    return templates.TemplateResponse("chats.html", {"request": request, "user": user})


@app.get("/chats/{session_id}", response_class=HTMLResponse)
async def chats_session_page(request: Request, session_id: str, user: dict = Depends(get_current_user, use_cache=False)):
    # Reuse the same template; the client JS will load messages
    return templates.TemplateResponse("chats.html", {"request": request, "user": user, "session_id": session_id})

@app.get("/compare", response_class=HTMLResponse)
async def compare_page(request: Request, user: dict = Depends(get_current_user, use_cache=False)):
    return templates.TemplateResponse("compare.html", {"request": request, "user": user})

@app.on_event("startup")
async def startup_event():
    await create_default_admin()

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, user: dict = Depends(get_current_user, use_cache=False)):
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})

@app.get("/research", response_class=HTMLResponse)
async def research_page(request: Request):
    return templates.TemplateResponse("research.html", {"request": request})

@app.get("/enhanced-research", response_class=HTMLResponse)
async def enhanced_research_page(request: Request):
    return templates.TemplateResponse("enhanced_research.html", {"request": request})


@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    return templates.TemplateResponse("portfolio.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, user: dict = Depends(get_current_user, use_cache=False)):
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})


# Add a GET logout endpoint to support header/logout links that use GET
@app.get("/api/auth/logout")
async def logout_get(request: Request):
    from fastapi.responses import RedirectResponse
    response = RedirectResponse(url="/login")
    # Delete auth cookie if present
    response.delete_cookie("access_token")
    return response

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard_page(request: Request, user: dict = Depends(get_current_user, use_cache=False)):
    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user})

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users_page(request: Request):
    return templates.TemplateResponse("admin/users.html", {"request": request})

@app.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics_page(request: Request):
    return templates.TemplateResponse("admin/analytics.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "AGENSTOCK API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)