#!/usr/bin/env python3
"""
LexaAI Backend (FastAPI) — Production version with Cloudflare support
"""
from __future__ import annotations

import logging
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import quote

from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv

# Import enhanced retrieval with resilient loading
try:
    from app.retrieval import enhanced_search
except Exception as e:
    logging.warning(f"Could not import enhanced_search: {e}")
    enhanced_search = None

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lexa-backend")

# ---------- Paths / Config ----------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Root data folder
DATA_ROOT = "/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/Backend_FastAPI"
CHROMA_ENV = os.getenv("LEXA_CHROMA_PATH", "chroma_db")
CHROMA_PATH = CHROMA_ENV if os.path.isabs(CHROMA_ENV) else os.path.join(DATA_ROOT, CHROMA_ENV)

# Branding/settings storage
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = STORAGE_DIR / "settings.json"
BRANDING_DIR = STORAGE_DIR / "branding"
BRANDING_DIR.mkdir(parents=True, exist_ok=True)

# Auth
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Krypt0n!t3")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBasic()

# Session management
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
signer = TimestampSigner(SECRET_KEY)

app = FastAPI(title="LexaAI Backend", docs_url="/api/docs", redoc_url="/api/redoc", openapi_url="/api/openapi.json")

# ---------- CORS with Cloudflare Access support ----------
ALLOWED_ORIGINS = [
    "https://lexaai.bizbots24.com",
    "https://bizbots24.cloudflareaccess.com",  # Cloudflare Access origin
    "http://127.0.0.1:8081",
    "http://localhost:8081",
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "")
MAX_SOURCES = 3

def build_file_url(request: Request, source_doc: str, page_number: int = 1) -> str:
    """Build proxy-safe link for a stored file with page fragments for PDFs."""
    xfproto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    xfhost  = (request.headers.get("x-forwarded-host")  or "").split(",")[0].strip()

    if xfhost:
        base = f"{xfproto or request.url.scheme}://{xfhost}"
        chosen = "xfhost"
    elif PUBLIC_HOST:
        base = PUBLIC_HOST.rstrip("/")
        chosen = "public_host"
    else:
        base = str(request.base_url).rstrip("/")
        chosen = "base_url"

    logger.info(f"build_file_url base={base} via={chosen}")

    safe = quote(source_doc)
    url  = f"{base}/files/{safe}"
    
    # Ensure PDFs jump to the exact page
    if page_number and str(source_doc).lower().endswith(".pdf"):
        if "#page=" not in url and "page=" not in url:
            url = f"{url}#page={page_number}"
    
    return url

def load_settings() -> Dict[str, Any]:
    """Load settings from storage."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Error loading settings: {e}")
    return {}

def save_settings(settings: Dict[str, Any]) -> None:
    """Save settings to storage."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving settings: {e}")

def verify_password(password: str) -> bool:
    """Verify admin password."""
    return password == ADMIN_PASSWORD

def create_session_token() -> str:
    """Create a session token."""
    payload = {"user": "admin", "timestamp": time.time()}
    return signer.sign(json.dumps(payload))

def verify_session_token(token: str) -> bool:
    """Verify session token."""
    try:
        payload = signer.unsign(token, max_age=86400)  # 24 hours
        data = json.loads(payload)
        return data.get("user") == "admin"
    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        return False

# ---------- Auth Dependency ----------
def require_admin_session(request: Request) -> bool:
    """Require valid admin session."""
    session_cookie = request.cookies.get("lexa_session")
    if not session_cookie or not verify_session_token(session_cookie):
        raise HTTPException(status_code=401, detail="Authentication required")
    return True

# ---------- Models ----------
class LoginRequest(BaseModel):
    password: str

class ChatRequest(BaseModel):
    query: str

# ---------- API Routes ----------

@app.get("/health")
@app.get("/healthz") 
@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "lexa-backend"}

@app.get("/api/admin/settings/public/branding")
def get_public_branding():
    """Get public branding settings."""
    settings = load_settings()
    branding = settings.get("branding", {})
    return {
        "status": "ok",
        "branding": {
            "appName": branding.get("appName", "LexaAI"),
            "tagline": branding.get("tagline", "Your AI Assistant"),
            "primaryColor": branding.get("primaryColor", "#3B82F6"),
            "logoUrl": branding.get("logoUrl", "")
        }
    }

@app.post("/admin/login")
@app.post("/auth/login")
def admin_login(request: Request, login_data: LoginRequest):
    """Admin login endpoint."""
    if not verify_password(login_data.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    token = create_session_token()
    
    response = JSONResponse({
        "success": True,
        "message": "Logged in successfully"
    })
    
    # Set session cookie with proper attributes for Cloudflare
    response.set_cookie(
        key="lexa_session",
        value=token,
        max_age=86400,  # 24 hours
        httponly=True,
        secure=True,  # Required for HTTPS
        samesite="lax",  # Allow cross-site requests from same origin
        domain=".bizbots24.com"  # Allow across subdomains
    )
    
    return response

@app.post("/admin/logout")
@app.post("/auth/logout")  
def admin_logout():
    """Admin logout endpoint."""
    response = JSONResponse({"success": True, "message": "Logged out"})
    response.delete_cookie("lexa_session")
    return response

@app.get("/admin/me")
@app.get("/auth/me")
def get_current_user(request: Request, _: bool = Depends(require_admin_session)):
    """Get current user info."""
    return {"user": "admin", "authenticated": True}

@app.get("/api/chat/")
def chat_endpoint(request: Request, query: str = Query(..., description="User query")):
    """Chat endpoint with enhanced retrieval and page-accurate sources."""
    if not query.strip():
        return {"response": "Query cannot be empty.", "sources": []}

    if not enhanced_search:
        return {"response": "Search functionality is not available.", "sources": []}

    try:
        # Use enhanced retrieval
        result = enhanced_search(query)
        enhanced_answer = result["answer"]
        enhanced_sources = result["sources"]
    except Exception as e:
        logger.error(f"Enhanced search error: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced search error: {e}")

    # Convert enhanced sources to UI format with max 3 sources
    sources = []
    seen = set()
    
    for src in (enhanced_sources or [])[:3]:  # Hard cap at 3 sources
        file_name = src.get("file_name", "Unknown")
        page = src.get("page", 1)
        url = build_file_url(request, file_name, page)
        
        # Safety-net: guarantee page-targeted PDF URLs
        if file_name.lower().endswith(".pdf") and page and "#page=" not in url and "page=" not in url:
            url = f"{url}#page={page}"
        
        if url in seen:
            continue
            
        name = f"{file_name} (p.{page})" if file_name.lower().endswith(".pdf") else file_name
        sources.append({"name": name, "url": url})
        seen.add(url)

    # If enhanced search found no information, return early
    if "couldn't find relevant information" in enhanced_answer.lower():
        return {"response": "I could not find relevant information in my database.", "sources": []}

    return {
        "response": enhanced_answer,
        "sources": sources
    }

@app.post("/api/chat/")
def chat_endpoint_post(request: Request, chat_data: ChatRequest):
    """POST version of chat endpoint."""
    return chat_endpoint(request, chat_data.query)

# Add a fallback for any missing endpoints that might be expected
@app.get("/query/")
def legacy_query(request: Request, query: str = Query(...)):
    """Legacy query endpoint - redirect to chat."""
    return chat_endpoint(request, query)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8600)