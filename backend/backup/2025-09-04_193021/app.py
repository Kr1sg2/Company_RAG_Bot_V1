#!/usr/bin/env python3
"""
LexaAI Backend (FastAPI) — Clean production version
"""
from __future__ import annotations

import logging
import os
import json
import time
from pathlib import Path
from typing import Dict, Any
from urllib.parse import quote

from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from pydantic import BaseModel
from dotenv import load_dotenv

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lexa-backend")

# ---------- Paths / Config ----------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Auth
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Krypt0n!t3")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "")

# Storage
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = STORAGE_DIR / "settings.json"

# Session management
signer = TimestampSigner(SECRET_KEY)

# Import enhanced search with error handling
enhanced_search = None
try:
    from lexa_app.retrieval import enhanced_search

    logger.info("✅ Enhanced search imported successfully")
except Exception as e:
    logger.warning(f"Enhanced search not available: {e}")

# ---------- FastAPI app ----------
app = FastAPI(
    title="LexaAI Backend",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# ---------- CORS ----------
ALLOWED_ORIGINS = [
    "https://lexaai.bizbots24.com",
    "https://bizbots24.cloudflareaccess.com",
    "http://127.0.0.1:8081",
    "http://localhost:8081",
    "http://localhost:5173",
]

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(
    CORSMiddleware,
    # Accept local origins for local development
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Helper Functions ----------
def build_file_url(request: Request, source_doc: str, page_number: int = 1) -> str:
    """Build proxy-safe link for a stored file with page fragments for PDFs."""
    xfproto = (request.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    xfhost = (request.headers.get("x-forwarded-host") or "").split(",")[0].strip()

    if xfhost:
        base = f"{xfproto or request.url.scheme}://{xfhost}"
    elif PUBLIC_HOST:
        base = PUBLIC_HOST.rstrip("/")
    else:
        base = str(request.base_url).rstrip("/")

    safe = quote(source_doc)
    url = f"{base}/files/{safe}"

    # Ensure PDFs jump to the exact page
    if page_number and str(source_doc).lower().endswith(".pdf"):
        if "#page=" not in url and "page=" not in url:
            url = f"{url}#page={page_number}"

    return url


def load_settings() -> Dict[str, Any]:
    """Load settings from storage."""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


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
        payload = signer.unsign(token, max_age=86400)
        data = json.loads(payload)
        return data.get("user") == "admin"
    except (BadSignature, SignatureExpired, json.JSONDecodeError):
        return False


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
    return branding


@app.get("/api/admin/settings/branding")
def get_admin_branding():
    """Get admin branding settings (same as public in local mode)."""
    settings = load_settings()
    branding = settings.get("branding", {})
    return branding


@app.put("/api/admin/settings/branding")
def put_admin_branding(branding_data: dict):
    """Save branding settings (no auth required in local mode)."""
    try:
        settings = load_settings()
        settings["branding"] = branding_data

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=2)

        return branding_data
    except Exception as e:
        logger.error(f"Failed to save branding: {e}")
        raise HTTPException(status_code=500, detail="Failed to save branding settings")


@app.post("/admin/login")
@app.post("/auth/login")
@app.post("/api/admin/login")
@app.post("/api/auth/login")
def admin_login(request: Request, login_data: LoginRequest):
    """Admin login endpoint (no password required in local mode)."""
    # Skip password verification in local mode
    # if not verify_password(login_data.password):
    #     raise HTTPException(status_code=401, detail="Invalid password")

    token = create_session_token()
    response = JSONResponse({"success": True, "message": "Logged in successfully"})

    # Set session cookie with proper attributes for local development
    response.set_cookie(
        key="lexa_session",
        value=token,
        max_age=86400,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    return response


@app.post("/admin/logout")
@app.post("/auth/logout")
@app.post("/api/admin/logout")
@app.post("/api/auth/logout")
def admin_logout():
    """Admin logout endpoint."""
    response = JSONResponse({"success": True, "message": "Logged out"})
    response.delete_cookie("lexa_session")
    return response


@app.get("/admin/me")
@app.get("/auth/me")
@app.get("/api/admin/me")
@app.get("/api/auth/me")
def get_current_user(request: Request):
    """Get current user info (no auth required in local mode)."""
    return {"user": "admin", "authenticated": True}


@app.get("/api/chat/")
def chat_endpoint(request: Request, query: str = Query(..., description="User query")):
    """Chat endpoint with enhanced retrieval and page-accurate sources."""
    if not query.strip():
        return {"response": "Query cannot be empty.", "sources": []}

    if not enhanced_search:
        return {"response": "Search functionality is not available.", "sources": []}

    try:
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
        if (
            file_name.lower().endswith(".pdf")
            and page
            and "#page=" not in url
            and "page=" not in url
        ):
            url = f"{url}#page={page}"

        if url in seen:
            continue

        name = (
            f"{file_name} (p.{page})"
            if file_name.lower().endswith(".pdf")
            else file_name
        )
        sources.append({"name": name, "url": url})
        seen.add(url)

    # If enhanced search found no information, return early
    if "couldn't find relevant information" in enhanced_answer.lower():
        return {
            "response": "I could not find relevant information in my database.",
            "sources": [],
        }

    return {"response": enhanced_answer, "sources": sources}


@app.post("/api/chat")
@app.post("/api/chat/")
def chat_endpoint_post(request: Request, chat_data: ChatRequest):
    """Chat endpoint for POST requests with JSON body."""
    return chat_endpoint(request, chat_data.query)


@app.get("/query/")
def legacy_query(request: Request, query: str = Query(...)):
    """Legacy query endpoint."""
    return chat_endpoint(request, query)


if __name__ == "__main__":
    print(f"App instance: {app}")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8600)
