"""
LexaAI Backend (FastAPI) — merged & fixed
- Robust RAG: ChromaDB + OpenAI embeddings (reads PDF/DOCX/XLSX/CSV/TXT)
- Website & single-page ingest (robots-aware, safety caps) -> indexes immediately
- Branding/settings + logo upload
- Safe source links honoring incoming host/scheme
- Admin-protected uploads/deletes; soft-delete to trash
- Enum fix for FastAPI params; guards for token/size
- Filenames normalized to hyphens (no underscores); background scan auto-renames
- NEW: /admin/login, /admin/me, /admin/logout (and /auth/* aliases for backward compat)
"""
from __future__ import annotations

import logging
import os
import io
import json
import time
import threading
import shutil
import re
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request, Query, Body, APIRouter, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic
from fastapi.responses import JSONResponse

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from itsdangerous import TimestampSigner, BadSignature, SignatureExpired
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from urllib.parse import urlparse, urljoin, quote

# Import new settings store modules
from settings_store import (
    load_settings,
    save_settings,
    extract_branding_fields,
    extract_ai_fields,
    extract_full_settings,
    update_branding_fields,
    update_ai_fields,
    update_full_settings
)
from migrate_settings import migrate_once

# ---------- Optional extractors ----------
try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

try:
    import pytesseract  # OCR
except Exception:
    pytesseract = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    from docx import Document
except Exception:
    Document = None

try:
    from PIL import Image
except Exception:
    Image = None

# ---------- Logging ----------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lexa-backend")

# ---------- Paths / Config ----------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # allow OPENAI_* etc from .env

# Root data folder (matches your existing structure)
DATA_ROOT = "/home/bizbots24/Company_Chatbot_Files/Lexa_AI_V2/Backend_FastAPI"
WATCH_DIRECTORY = os.path.join(DATA_ROOT, "Database")
CHROMA_PATH = os.path.join(DATA_ROOT, "chroma_db")
DOCUMENT_IDS_FILE = os.path.join(DATA_ROOT, "document_ids.json")

os.makedirs(WATCH_DIRECTORY, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

# Branding/settings storage
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = STORAGE_DIR / "settings.json"
BRANDING_DIR = STORAGE_DIR / "branding"
BRANDING_DIR.mkdir(parents=True, exist_ok=True)

# Auth
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Krypt0n!t3")  # change for prod

# Public host fallback for file URLs
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "").strip()

# OpenAI & knobs (fallback from env, but use settings when available)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")  # optional proxy/base
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.5"))

SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.55"))

# Helper to get AI settings from store with env fallbacks
def get_ai_settings() -> Dict[str, Any]:
    """Get current AI settings from store with environment fallbacks."""
    settings = load_settings()
    ai_settings = extract_ai_fields(settings)
    
    # Apply environment fallbacks for missing values
    ai_settings.setdefault("model", OPENAI_MODEL)
    ai_settings.setdefault("temperature", OPENAI_TEMPERATURE)
    ai_settings.setdefault("strictness", 1)
    
    return ai_settings

# Chat/guardrails
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "4000"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "800"))
MAX_SOURCES = int(os.getenv("MAX_SOURCES", "5"))

# Crawl guardrails
CRAWL_MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "50"))
CRAWL_MAX_DEPTH = int(os.getenv("CRAWL_MAX_DEPTH", "2"))
CRAWL_MAX_TOTAL_BYTES = int(os.getenv("CRAWL_MAX_TOTAL_BYTES", str(15 * 1024 * 1024)))  # 15 MB
CRAWL_THROTTLE_SECONDS = float(os.getenv("CRAWL_THROTTLE_SECONDS", "0.3"))
USER_AGENT = "LexaAI-Ingest/1.0 (+https://example.invalid)"

# Allowed file types for indexing/listing
ALLOWED_EXTS = {".pdf", ".txt", ".md", ".docx", ".xlsx", ".csv"}

# ---------- FastAPI app ----------
app = FastAPI(title="LexaAI Backend")

# --- DEBUG AUTH TESTING ---
from app_security import require_admin_basic

@app.post("/api/auth_echo/")  # simple POST protected by the same guard
def auth_echo(_: bool = Depends(require_admin_basic)):
    return {"ok": True}

# --- CORS ---
_frontend_origins_env = os.getenv("FRONTEND_ORIGIN", "http://localhost:8080")
ALLOWED_ORIGINS = [o.strip() for o in _frontend_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for clickable sources & logos)
app.mount("/files", StaticFiles(directory=WATCH_DIRECTORY), name="files")
app.mount("/branding", StaticFiles(directory=str(BRANDING_DIR)), name="branding")

# ---------- Auth (HTTP Basic object for parsing only) ----------
security = HTTPBasic()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
USER_CREDENTIALS = {"admin": pwd_context.hash(ADMIN_PASSWORD)}  # not used directly; retained for compat

# ---------- Name normalization (hyphens everywhere) ----------
def hyphen_name(name: str) -> str:
    """
    Normalize to lowercase, spaces/underscores/other punctuation -> '-', collapse repeats,
    keep extension dot(s), and trim leading/trailing hyphens.
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", "-", name)               # spaces -> -
    name = name.replace("_", "-")                  # underscores -> -
    name = re.sub(r"[^a-z0-9.-]+", "-", name)      # other punctuation -> -
    name = re.sub(r"-{2,}", "-", name)             # collapse --
    name = name.strip("-")
    return name[:200] or "file"

# ==== AUTH: cookie session (keeps Basic as fallback) ====
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-prod")
SESSION_COOKIE = "lexa_session"
SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE", "604800"))  # 7 days
signer = TimestampSigner(SECRET_KEY)

def _set_session_cookie(response: JSONResponse, username: str, secure: bool):
    token = signer.sign(username.encode("utf-8")).decode("utf-8")
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=SESSION_MAX_AGE,
        httponly=True,
        secure=secure,     # True only when serving HTTPS (or behind TLS terminator)
        samesite="lax",
        path="/",
    )

def _clear_session_cookie(response: JSONResponse):
    response.delete_cookie(SESSION_COOKIE, path="/")

def _get_user_from_cookie(request: Request) -> str | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    try:
        return signer.unsign(token, max_age=SESSION_MAX_AGE).decode("utf-8")
    except (BadSignature, SignatureExpired):
        return None

def require_admin(request: Request):
    # 1) Cookie session
    user = _get_user_from_cookie(request)
    if user == "admin":
        return user
    # 2) Fallback: HTTP Basic (backwards compatible with older tools)
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("basic "):
        import base64
        raw = auth.split(" ", 1)[1]
        try:
            user_pass = base64.b64decode(raw).decode("utf-8")
            if ":" in user_pass:
                u, pw = user_pass.split(":", 1)
                if u == "admin" and pw == os.getenv("ADMIN_PASSWORD", "Krypt0n!t3"):
                    return "admin"
        except Exception:
            pass
    raise HTTPException(status_code=401, detail="Unauthorized")

class LoginRequest(BaseModel):
    username: str
    password: str

# ----- Admin session endpoints (canonical: /auth/*) with /admin/* aliases -----

def _password_ok(username: str, password: str) -> bool:
    """Single place to check creds; username is fixed to 'admin'."""
    return username == "admin" and password == os.getenv("ADMIN_PASSWORD", "Krypt0n!t3")

def _is_https_request(request: Request | None) -> bool:
    """Honor reverse-proxy headers when deciding Secure cookie."""
    if not request:
        return False
    xfproto = (request.headers.get("x-forwarded-proto") or "").lower()
    return xfproto.startswith("https") or (request.url.scheme == "https")

@app.post("/auth/login")
def auth_login(request: Request, payload: LoginRequest = Body(...)):
    if not _password_ok(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    resp = JSONResponse({"ok": True, "user": "admin"})
    _set_session_cookie(resp, "admin", secure=_is_https_request(request))
    return resp

@app.post("/auth/logout")
def auth_logout():
    resp = JSONResponse({"ok": True})
    _clear_session_cookie(resp)
    return resp

@app.get("/auth/me")
def auth_me(request: Request):
    user = _get_user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"user": user}

# ----- Backward-compatible aliases (/admin/*) -----

@app.post("/admin/login")
def admin_login_alias(request: Request, payload: LoginRequest = Body(...)):
    return auth_login(request, payload)

@app.post("/admin/logout")
def admin_logout_alias():
    return auth_logout()

@app.get("/admin/me")
def admin_me_alias(request: Request):
    return auth_me(request)

# ---------- Helpers ----------
def build_file_url(request: Request, source_doc: str, page_number: int = 1) -> str:
    """Build proxy-safe link for a stored file.
    Priority: X-Forwarded-Host → PUBLIC_HOST → request.base_url
    """
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

    # one-line debug (shows in server logs, safe – no secrets)
    logger.info(f"build_file_url base={base} via={chosen}")

    safe = quote(source_doc)
    url  = f"{base}/files/{safe}"
    return f"{url}#page={page_number}" if source_doc.lower().endswith(".pdf") else url

def clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))

def _is_supported(name: str) -> bool:
    return Path(name).suffix.lower() in ALLOWED_EXTS

# ---------- Settings / Branding ----------
@dataclass
class BrandingSettings:
    companyName: str = "LexaAI Company Chatbot"
    primaryColor: str = "#2563eb"
    accentColor: str = "#3b82f6"
    fontFamily: str = "system-ui"
    fontSize: int = 14
    foregroundColor: str = "#0F172A"
    mutedForegroundColor: str = "#64748B"
    themeMode: str = "system"               # light | dark | system
    companyLogoDataUrl: str | None = None
    backgroundImageDataUrl: str | None = None
    robotIconDataUrl: str | None = None
    uiHeader: str = "Closed-book RAG system - answers only from company documents"
    uiSubtitle: str = "Ask me anything about your company documents"
    uiPlaceholder: str = "Ask a question about your documents"

def _apply_branding_to_public_settings(branding: dict) -> dict:
    """Map branding fields to public settings format, supporting extended fields."""
    result = {}
    
    # Pass through all extended fields directly
    extended_fields = [
        "companyName", "logoDataUrl", "faviconUrl",
        "pageBackgroundColor", "pageBackgroundUrl", "chatCardBackgroundColor",
        "chatCardBackgroundUrl", "inputBackgroundColor",
        "fontFamily", "titleColor", "titleFontSize", "titleBold", "titleItalic",
        "taglineText", "taglineColor", "taglineFontSize", "taglineBold", "taglineItalic",
        "inputTextColor", "inputFontSize", "inputBold", "inputItalic",
        "userBubbleBg", "userTextColor", "userBold", "userItalic",
        "assistantTextColor", "assistantBold", "assistantItalic",
        "sendButtonBgColor", "sendButtonTextColor",
        "glowColor", "glowBlur", "glowSpread", "glowOpacity",
        "primaryColor", "accentColor", "mutedTextColor", "robotLogoDataUrl", "robotSize",
        "emptyStateText", "inputPlaceholder", "fontSize"
    ]
    
    # Track which URL fields are explicitly present (including if set to None/cleared)
    explicitly_present_urls = {field for field in ["pageBackgroundUrl", "chatCardBackgroundUrl"] if field in branding}
    
    # Pass through all extended fields that exist
    for field in extended_fields:
        if field in branding:
            # For URL fields that are explicitly present, preserve null (cleared) state
            if field.endswith('Url') and field in explicitly_present_urls:
                result[field] = branding[field]  # Include even if None (cleared)
            # For non-URL fields or URL fields not explicitly set, only include non-None values
            elif branding[field] is not None:
                # Skip empty URL fields  
                if field.endswith('Url') and str(branding[field]).strip() == "":
                    continue
                result[field] = branding[field]
    
    # Legacy field mappings for backward compatibility
    if not result.get("companyName"):
        result["companyName"] = branding.get("title") or "LexaAI Company Chatbot"
    
    # Map legacy background/foreground objects (only if URLs not explicitly cleared)
    bg = branding.get("background") or {}
    fg = branding.get("foreground") or {}
    if not result.get("pageBackgroundColor") and bg.get("color"):
        result["pageBackgroundColor"] = bg["color"]
    # Only use legacy URL if field not explicitly present in branding (not explicitly cleared)
    if "pageBackgroundUrl" not in explicitly_present_urls and not result.get("pageBackgroundUrl") and bg.get("imageUrl"):
        result["pageBackgroundUrl"] = bg["imageUrl"]
    if not result.get("chatCardBackgroundColor") and fg.get("color"):
        result["chatCardBackgroundColor"] = fg["color"]
    # Only use legacy URL if field not explicitly present in branding (not explicitly cleared)
    if "chatCardBackgroundUrl" not in explicitly_present_urls and not result.get("chatCardBackgroundUrl") and fg.get("imageUrl"):
        result["chatCardBackgroundUrl"] = fg["imageUrl"]
    
    # Map legacy shadow object
    shadow = branding.get("shadow") or {}
    if not result.get("glowColor") and shadow.get("color"):
        result["glowColor"] = shadow["color"]
    if not result.get("glowBlur") and shadow.get("blur"):
        result["glowBlur"] = shadow["blur"]
    if not result.get("glowSpread") and shadow.get("spread"):
        result["glowSpread"] = shadow["spread"]
    if not result.get("glowOpacity") and shadow.get("opacity"):
        result["glowOpacity"] = shadow["opacity"]
    
    # Map legacy robot object
    robot = branding.get("robot") or {}
    if not result.get("robotLogoDataUrl") and robot.get("imageUrl"):
        result["robotLogoDataUrl"] = robot["imageUrl"]
    if not result.get("robotSize") and robot.get("size"):
        result["robotSize"] = robot["size"]
    
    # Map legacy text style objects
    tagline = branding.get("tagline") or {}
    if not result.get("fontFamily") and tagline.get("fontFamily"):
        result["fontFamily"] = tagline["fontFamily"]
    if not result.get("fontSize") and tagline.get("fontSize"):
        result["fontSize"] = tagline["fontSize"]
    
    # Map legacy favicon object
    favicon = branding.get("favicon") or {}
    if not result.get("faviconUrl") and favicon.get("url32"):
        result["faviconUrl"] = favicon["url32"]
    
    return result

def _to_public_settings(s: dict) -> dict:
    """Convert stored settings to PublicSettings canonical shape."""
    # Start with existing fields for backward compatibility
    result = {
        "companyName": s.get("companyName") or s.get("title") or "LexaAI Company Chatbot",
        "primaryColor": s.get("primaryColor") or "#2563eb",
        "accentColor": s.get("accentColor") or "#3b82f6",
        "fontFamily": s.get("fontFamily") or "system-ui",
        "fontSize": s.get("fontSize", 14),
        "logoDataUrl": s.get("logoDataUrl") or s.get("companyLogoDataUrl"),
        "taglineText": s.get("taglineText") or s.get("uiHeader")
                       or "Closed-book RAG system - answers only from company documents",
        "emptyStateText": s.get("emptyStateText") or s.get("uiSubtitle")
                       or "Ask me anything about your company documents!",
        "inputPlaceholder": s.get("inputPlaceholder") or s.get("uiPlaceholder")
                       or "Ask a question about your documents...",
        "foregroundColor": s.get("foregroundColor") or "#0f172a",
        "mutedForegroundColor": s.get("mutedForegroundColor") or "#64748b",
        "themeMode": s.get("themeMode") or "system",
        "robotLogoDataUrl": s.get("robotLogoDataUrl") or s.get("robotIconDataUrl"),
        "backgroundDataUrl": s.get("backgroundDataUrl") or s.get("backgroundImageDataUrl"),
    }
    
    # Apply branding fields if they exist (override/extend the base fields)
    branding_fields = _apply_branding_to_public_settings(s)
    result.update({k: v for k, v in branding_fields.items() if v is not None})
    
    return result

# Legacy settings functions (kept for compatibility - now directly using store functions)
# load_settings and save_settings are imported directly from settings_store

if not SETTINGS_FILE.exists():
    save_settings(asdict(BrandingSettings()))

# ---------- Health ----------
@app.get("/health")
@app.get("/healthz")
def health():
    return {"ok": True}

@app.get("/api/health")
def api_health():
    return {"ok": True}

# ---------- Simple FS listing ----------
def list_dir_files(d: str | Path) -> list[str]:
    files: list[str] = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if os.path.isfile(p) and _is_supported(name):
            files.append(name)
    return files

@app.get("/list_documents/")
def list_documents():
    files = []
    for name in sorted(os.listdir(WATCH_DIRECTORY)):
        path = os.path.join(WATCH_DIRECTORY, name)
        if os.path.isfile(path) and _is_supported(name):
            stat = os.stat(path)
            files.append({
                "name": name,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "type": Path(name).suffix.lower().lstrip('.') or 'unknown'
            })
    return {"stored_documents": [f["name"] for f in files], "documents": files}

@app.get("/count_documents/")
def count_documents():
    return {"document_count": len(list_dir_files(WATCH_DIRECTORY))}

@app.get("/preview_document/")
def preview_document(filename: str):
    """Preview the contents of a document (first 1000 characters)"""
    import os
    from pathlib import Path
    
    # Security check - ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    file_path = Path(WATCH_DIRECTORY) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # For text files, read and return content
        if filename.lower().endswith(('.txt', '.md')):
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(1000)  # First 1000 characters
                return {
                    "filename": filename,
                    "type": "text",
                    "content": content,
                    "truncated": len(content) == 1000
                }
        
        # For PDF files, attempt to extract text
        elif filename.lower().endswith('.pdf'):
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    content = ""
                    # Read first few pages
                    for i in range(min(3, len(pdf_reader.pages))):
                        content += pdf_reader.pages[i].extract_text() + "\n"
                        if len(content) > 1000:
                            break
                    return {
                        "filename": filename,
                        "type": "pdf", 
                        "content": content[:1000],
                        "truncated": len(content) > 1000,
                        "pages": len(pdf_reader.pages)
                    }
            except Exception:
                return {
                    "filename": filename,
                    "type": "pdf",
                    "content": "PDF content cannot be previewed",
                    "truncated": False
                }
        
        # For other files
        else:
            return {
                "filename": filename,
                "type": "binary",
                "content": f"File type not supported for preview: {filename}",
                "truncated": False
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

# ---------- RAG stack (Chroma + embeddings) ----------
from chromadb import PersistentClient
from langchain_openai import OpenAIEmbeddings

try:
    embeddings = OpenAIEmbeddings(
        openai_api_key=OPENAI_API_KEY,
        model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        openai_api_base=OPENAI_API_BASE,
    )
except TypeError:
    embeddings = OpenAIEmbeddings(  # older versions use base_url arg
        openai_api_key=OPENAI_API_KEY,
        model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
        base_url=OPENAI_API_BASE,
    )

chroma_client = PersistentClient(path=CHROMA_PATH)
db_collection = chroma_client.get_or_create_collection(name="documents")

# Track which documents are indexed
def load_document_ids() -> set[str]:
    if os.path.exists(DOCUMENT_IDS_FILE):
        try:
            with open(DOCUMENT_IDS_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_document_ids(ids: set[str]) -> None:
    with open(DOCUMENT_IDS_FILE, "w") as f:
        json.dump(sorted(list(ids)), f)

document_ids: set[str] = load_document_ids()

# ---------- Text splitting ----------
from langchain.text_splitter import RecursiveCharacterTextSplitter
splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)

def is_valid_chunk(chunk: str) -> bool:
    if len(chunk) < 30:
        return False
    printable_ratio = sum(c.isprintable() for c in chunk) / len(chunk)
    return printable_ratio > 0.6

# ---------- Extractors ----------
def extract_text_from_pdf(pdf_bytes: bytes) -> List[dict]:
    if not fitz:
        raise HTTPException(status_code=500, detail="PDF extraction requires PyMuPDF (pymupdf).")
    page_texts = []
    doc = fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf")
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text") or ""
        if not text.strip() and pytesseract and Image:
            # OCR fallback (handle alpha properly)
            pix = page.get_pixmap(alpha=False)
            mode = "RGBA" if getattr(pix, "alpha", False) else "RGB"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            if mode == "RGBA":
                img = img.convert("RGB")
            text = pytesseract.image_to_string(img)
        page_texts.append({"text": text or "", "page": page_num})
    return page_texts

def extract_text_from_docx(docx_bytes: bytes) -> List[dict]:
    if not Document:
        raise HTTPException(status_code=500, detail="DOCX extraction requires python-docx.")
    doc = Document(io.BytesIO(docx_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    filtered: list[str] = []
    prev_img = False
    for para in paragraphs:
        low = para.lower().strip()
        if "table of contents" in low or low == "contents":
            continue
        if prev_img and low == "click":
            prev_img = False
            continue
        if any(tag in low for tag in ("image", "figure", "graphic")):
            prev_img = True
            continue
        prev_img = False
        filtered.append(para)
    text = "\n".join(filtered) if filtered else ""
    return [{"text": text, "page": 1}] if text else []

def extract_text_from_xlsx(xlsx_bytes: bytes) -> List[dict]:
    if not pd:
        raise HTTPException(status_code=500, detail="XLSX extraction requires pandas.")
    excel_file = io.BytesIO(xlsx_bytes)
    df_sheets = pd.read_excel(excel_file, sheet_name=None, dtype=str)
    out: List[dict] = []
    for sheet_name, df in df_sheets.items():
        if df.empty:
            continue
        text = df.fillna("").to_string(index=False, header=False)
        out.append({"text": text, "page": sheet_name})
    return out

def extract_text_from_csv(csv_bytes: bytes) -> List[dict]:
    if not pd:
        raise HTTPException(status_code=500, detail="CSV extraction requires pandas.")
    csv_file = io.StringIO(csv_bytes.decode("utf-8", errors="ignore"))
    df = pd.read_csv(csv_file, dtype=str)
    if df.empty:
        return []
    text = df.fillna("").to_string(index=False, header=False)
    return [{"text": text, "page": 1}]

# ---------- Index helpers ----------
def add_document(pages: List[dict], doc_id: str, file_link: str):
    logger.info(f"Indexing document: {doc_id}")
    try:
        for page_data in pages:
            text = page_data.get("text", "") or ""
            page_number = page_data.get("page", 1)

            chunks = splitter.split_text(text)
            chunks = [c for c in chunks if c.strip() and is_valid_chunk(c)]
            if not chunks:
                continue

            vectors = embeddings.embed_documents(chunks)
            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}-p{page_number}-{i}"
                db_collection.add(
                    ids=[chunk_id],
                    embeddings=[vectors[i]],
                    metadatas=[{
                        "text": chunk,
                        "source_doc": doc_id,
                        "file_link": file_link,
                        "page": page_number
                    }]
                )

        document_ids.add(doc_id)
        save_document_ids(document_ids)
    except Exception as e:
        logger.exception(f"Indexing failed for {doc_id}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {e}")

def delete_document_from_db(doc_id: str):
    logger.info(f"Deleting from index: {doc_id}")
    try:
        db_collection.delete(where={"source_doc": doc_id})
        if doc_id in document_ids:
            document_ids.remove(doc_id)
            save_document_ids(document_ids)
    except Exception as e:
        logger.exception(f"Delete from DB failed for {doc_id}")
        raise HTTPException(status_code=500, detail=f"DB delete failed: {e}")

# ---------- Directory scan (auto-rename to hyphens) ----------
def scan_directory():
    current_files = set(os.listdir(WATCH_DIRECTORY))

    # Index new (with normalization/rename if needed)
    for name in sorted(current_files - document_ids):
        path = os.path.join(WATCH_DIRECTORY, name)
        if not os.path.isfile(path) or not _is_supported(name):
            continue

        # Normalize filename to hyphen style
        final_name = ensure_hyphen_file(WATCH_DIRECTORY, name)
        if final_name != name:
            path = os.path.join(WATCH_DIRECTORY, final_name)

        with open(path, "rb") as f:
            data = f.read()
        ext = Path(final_name).suffix.lower()
        if ext == ".pdf":
            pages = extract_text_from_pdf(data)
        elif ext in {".txt", ".md"}:
            pages = [{"text": data.decode("utf-8", errors="ignore"), "page": 1}]
        elif ext == ".docx":
            pages = extract_text_from_docx(data)
        elif ext == ".xlsx":
            pages = extract_text_from_xlsx(data)
        elif ext == ".csv":
            pages = extract_text_from_csv(data)
        else:
            continue
        # store a relative file link; UI will rebuild absolute via request later
        file_link = f"/files/{quote(final_name)}"
        add_document(pages, final_name, file_link)

    # Purge removed
    for name in list(document_ids - current_files):
        delete_document_from_db(name)

def periodic_scan():
    while True:
        try:
            scan_directory()
        except Exception:
            logger.exception("Periodic scan failed")
        time.sleep(8 * 60 * 60)

@app.on_event("startup")
def _start_scan_thread():
    # Do an initial scan immediately, then start the periodic thread
    try:
        scan_directory()
    except Exception:
        logger.exception("Initial scan failed")
    threading.Thread(target=periodic_scan, daemon=True).start()

# ---------- Upload / Delete / Scan / Reset ----------
def ensure_hyphen_file(dirpath: str, filename: str) -> str:
    """
    If filename needs normalization, rename on disk (avoid collisions).
    Return the final filename.
    """
    normalized = hyphen_name(filename)
    src = os.path.join(dirpath, filename)
    dst = os.path.join(dirpath, normalized)
    if filename == normalized:
        return filename
    # resolve collision
    if os.path.exists(dst):
        stem, ext = os.path.splitext(normalized)
        i = 1
        while True:
            cand = f"{stem}-{i}{ext}"
            if not os.path.exists(os.path.join(dirpath, cand)):
                dst = os.path.join(dirpath, cand)
                normalized = cand
                break
            i += 1
    try:
        os.replace(src, dst)
        logger.info(f"Renamed file: '{filename}' -> '{normalized}'")
        return normalized
    except Exception:
        # If move fails for any reason, fall back to original name
        logger.warning(f"Failed to rename '{filename}', indexing as-is.")
        return filename

## MOVED under /api via guarded admin router
# @app.post("/upload/")
# async def upload_documents(
#     request: Request,
#     files: List[UploadFile] = File(...),
#     username: str = Depends(require_admin),
# ):
#     uploaded: list[str] = []
#     for file in files:
#         # Normalize name right away
#         name = hyphen_name(file.filename or "file")
#         if not _is_supported(name):
#             logger.warning(f"Unsupported file type: {name}")
#             continue
#         dest = os.path.join(WATCH_DIRECTORY, name)
# 
#         # Collision-safe target
#         if os.path.exists(dest):
#             stem, ext = os.path.splitext(name)
#             i = 1
#             while os.path.exists(os.path.join(WATCH_DIRECTORY, f"{stem}-{i}{ext}")):
#                 i += 1
#             name = f"{stem}-{i}{ext}"
#             dest = os.path.join(WATCH_DIRECTORY, name)
# 
#         data = await file.read()
#         with open(dest, "wb") as f:
#             f.write(data)
# 
#         ext = Path(name).suffix.lower()
#         if ext == ".pdf":
#             pages = extract_text_from_pdf(data)
#         elif ext in {".txt", ".md"}:
#             pages = [{"text": data.decode("utf-8", errors="ignore"), "page": 1}]
#         elif ext == ".docx":
#             pages = extract_text_from_docx(data)
#         elif ext == ".xlsx":
#             pages = extract_text_from_xlsx(data)
#         elif ext == ".csv":
#             pages = extract_text_from_csv(data)
#         else:
#             continue
# 
#         # reindex (delete prior chunks if re-upload)
#         if name in document_ids:
#             delete_document_from_db(name)
# 
#         file_link = build_file_url(request, name, 1)
#         add_document(pages, name, file_link)
#         uploaded.append(name)
# 
#     return {"message": "Documents indexed successfully", "files": uploaded}

## MOVED under /api via guarded admin router
# @app.delete("/delete/")
# def delete_document(
#     doc_id: str,
#     username: str = Depends(require_admin),
# ):
#     """Soft delete on disk to storage/trash + remove from DB."""
#     # Remove from DB first
#     delete_document_from_db(doc_id)
# 
#     src = os.path.join(WATCH_DIRECTORY, doc_id)
#     if not os.path.exists(src):
#         return {"message": f"Document '{doc_id}' removed from index (file not on disk)."}
# 
#     trash_dir = STORAGE_DIR / "trash"
#     trash_dir.mkdir(parents=True, exist_ok=True)
#     dst = trash_dir / f"{int(time.time())}_{doc_id}"
#     shutil.move(src, dst)
#     return {"message": f"Document '{doc_id}' moved to trash and removed from index."}

## MOVED under /api via guarded admin router
# @app.post("/scan/")
# def manual_scan(username: str = Depends(require_admin)):
#     scan_directory()
#     return {"message": "Directory scanned successfully."}

## MOVED under /api via guarded admin router
# @app.post("/reset_memory/")
# def reset_memory(username: str = Depends(require_admin)):
#     """Blow away ChromaDB & reinit (does not delete files)."""
#     global chroma_client, db_collection, document_ids
#     try:
#         chroma_client.reset()
#         time.sleep(1)
#     except Exception:
#         pass
# 
#     shutil.rmtree(CHROMA_PATH, ignore_errors=True)
#     os.makedirs(CHROMA_PATH, exist_ok=True)
# 
#     chroma_client = PersistentClient(path=CHROMA_PATH)
#     db_collection = chroma_client.get_or_create_collection(name="documents")
# 
#     document_ids.clear()
#     save_document_ids(document_ids)
# 
#     return {"message": "Memory reset successfully."}

# ---------- Query (snippet list) ----------
@app.get("/query/")
@app.get("/api/query")
def query_snippets(query: str, request: Request):
    if not query.strip():
        return {"response": [{"text": "Query cannot be empty.", "file_link": None}]}
    try:
        from math import isfinite
        qv = embeddings.embed_query(query)
        res = db_collection.query(
            query_embeddings=[qv],
            n_results=8,
            include=["metadatas", "distances"]
        )
        candidates: list[tuple[float, dict]] = []
        for md_list, dist_list in zip(res.get("metadatas", []) or [], res.get("distances", []) or []):
            for md, d in zip(md_list or [], dist_list or []):
                d = d if (d is not None and isfinite(d)) else 1.0
                sim = 1 - d
                if md:
                    candidates.append((sim, md))
        if not candidates:
            return {"response": [{"text": "No relevant results found.", "file_link": None}]}

        def _mtime(md):
            try:
                return os.path.getmtime(os.path.join(WATCH_DIRECTORY, md.get("source_doc", "")))
            except Exception:
                return 0.0

        candidates.sort(key=lambda t: (t[0], _mtime(t[1])), reverse=True)
        passed = [md for sim, md in candidates if sim >= SIMILARITY_THRESHOLD]
        picked = (passed or [md for _, md in candidates[:5]])[:5]

        out = []
        for md in picked:
            source_doc = md.get("source_doc", "Unknown")
            text = (md.get("text") or "")[:1500]
            page = int(md.get("page", 1))
            url = build_file_url(request, source_doc, page)
            name = f"{source_doc} (p.{page})" if source_doc.lower().endswith(".pdf") else source_doc
            out.append({"text": text, "file_link": url, "name": name})
        return {"response": out}
    except Exception as e:
        logger.exception("Query failed")
        return {"response": [{"text": f"Error: {e}", "file_link": None}]}

# ---------- Chat (LLM over retrieved context) ----------
class ChatStyle(str, Enum):
    paragraph = "paragraph"
    bullets = "bullets"
    hybrid = "hybrid"

class ChatTone(str, Enum):
    friendly = "friendly"
    neutral = "neutral"
    formal = "formal"

class ChatLength(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"

class ChatResponse(BaseModel):
    response: str
    sources: list[dict] = Field(default_factory=list)

class ChatIn(BaseModel):
    message: str

@app.post("/chat/", response_model=ChatResponse)
def chat_with_openai(
    request: Request,
    query: str = Query(..., alias="query"),
    style: ChatStyle = Query(ChatStyle.paragraph),
    tone: ChatTone = Query(ChatTone.friendly),
    length: ChatLength = Query(ChatLength.medium),
):
    """Original chat endpoint with query parameters."""
    if not query.strip():
        return {"response": "Query cannot be empty.", "sources": []}

    # Retrieve context
    try:
        qv = embeddings.embed_query(query)
        res = db_collection.query(
            query_embeddings=[qv],
            n_results=6,
            include=["metadatas", "distances"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    snippets: list[str] = []
    sources: list[dict] = []
    seen = set()

    for md_list, _dist_list in zip(res.get("metadatas", []) or [], res.get("distances", []) or []):
        for md in md_list or []:
            txt = (md.get("text") or "").strip()
            if txt:
                snippets.append(txt[:900] + ("..." if len(txt) > 900 else ""))
            src = md.get("source_doc")
            if not src:
                continue
            page = int(md.get("page", 1))
            url = build_file_url(request, src, page)
            if url in seen:
                continue
            name = f"{src} (p.{page})" if src.lower().endswith(".pdf") else src
            sources.append({"name": name, "url": url})
            seen.add(url)
            if len(sources) >= MAX_SOURCES:
                break

    if not snippets:
        return {"response": "I could not find relevant information in my database.", "sources": []}

    # Build message for the model
    style_rules = {
        "paragraph": "Write in natural, conversational prose using full sentences.",
        "bullets": "Use concise bullet points for each idea.",
        "hybrid": "Start with 2-3 sentences, then a short bullet list of key points.",
    }
    length_targets = {
        "short": "Aim for ~100–150 words.",
        "medium": "Aim for ~200–350 words.",
        "long": "Aim for ~500–700 words with helpful detail.",
    }
    tone_map = {
        "friendly": "Use a warm, helpful tone.",
        "neutral": "Use a clear, professional tone.",
        "formal": "Use a formal, precise tone.",
    }

    system_message = (
        "You are a company assistant. Only use the provided context to answer questions. "
        "If no relevant information is available, say 'I could not find relevant information in my database.'\n\n"
        f"{tone_map[tone.value]} {style_rules[style.value]} {length_targets[length.value]}\n"
        "Do not invent facts not present in the context.\n\n"
        "Context:\n" + "\n\n".join(snippets) + "\n\n"
        "User Question: " + query + "\n"
        "Provide a precise and relevant answer strictly based on the context."
    )

    if not OPENAI_API_KEY:
        return {"response": "OpenAI API key is not configured on the server.", "sources": sources}

    # Get current AI settings
    ai_settings = get_ai_settings()
    
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
    resp = client.chat.completions.create(
        model=ai_settings.get("model", OPENAI_MODEL),
        messages=[{"role": "system", "content": system_message},
                  {"role": "user", "content": query}],
        temperature=float(ai_settings.get("temperature", OPENAI_TEMPERATURE)),
        max_tokens=int(ai_settings.get("max_tokens", MAX_OUTPUT_TOKENS)),
        top_p=1.0,  # Keep deterministic
        frequency_penalty=0,
        presence_penalty=0,
    )
    answer = resp.choices[0].message.content.strip()
    return {"response": answer, "sources": sources}

@app.post("/api/chat", response_model=ChatResponse)
def api_chat_post(request: Request, payload: ChatIn):
    """JSON API endpoint for chat - accepts POST with message in body."""
    return chat_with_openai(
        request=request,
        query=payload.message,
        style=ChatStyle.paragraph,
        tone=ChatTone.friendly,
        length=ChatLength.medium
    )

# ---------- Admin: settings/branding ----------
@app.get("/admin/settings")
def get_settings(public: bool = False):
    s = load_settings()
    if public:
        public_settings = _to_public_settings(s)
        # Emergency hotfix toggle to force clear URLs
        if os.getenv("BRANDING_FORCE_CLEAR") == "1":
            public_settings["pageBackgroundUrl"] = None
            public_settings["chatCardBackgroundUrl"] = None
        return public_settings
    return s

# New unified settings endpoints
# DEPRECATED: use /api/admin/settings/branding
@app.get("/admin/settings/branding")
def get_branding_settings():
    """Get only branding-related settings."""
    return extract_branding_fields(load_settings())

# DEPRECATED: use /api/admin/settings/ai
@app.get("/admin/settings/ai")
def get_ai_settings_endpoint():
    """Get only AI-related settings."""
    return extract_ai_fields(load_settings())

# DEPRECATED: use /api/admin/settings
@app.get("/admin/settings/full")
def get_full_settings():
    """Get complete settings (branding + AI)."""
    return extract_full_settings(load_settings())

# DEPRECATED: use /api/admin/settings/branding
@app.put("/admin/settings/branding")
def put_branding_settings(payload: dict, _: str = Depends(require_admin)):
    """Update only branding settings, preserving AI settings."""
    return update_branding_fields(payload)

# DEPRECATED: use /api/admin/settings/ai
@app.put("/admin/settings/ai")
def put_ai_settings(payload: dict, _: str = Depends(require_admin)):
    """Update only AI settings, preserving branding settings."""
    return update_ai_fields(payload)

# DEPRECATED: use /api/admin/settings
@app.put("/admin/settings/full")
def put_full_settings(payload: dict, _: str = Depends(require_admin)):
    """Update complete settings."""
    return update_full_settings(payload)

## MOVED under /api via guarded admin router
# @app.put("/admin/settings")
# def put_settings(payload: dict, username: str = Depends(require_admin)):
#     s = load_settings()
#     s.update(payload or {})
#     save_settings(s)
#     return s
# 
# @app.post("/admin/branding/logo")
# async def upload_logo(file: UploadFile = File(...), username: str = Depends(require_admin)):
#     ext = Path(file.filename or "").suffix.lower() or ".png"
#     if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
#         raise HTTPException(status_code=400, detail="Unsupported image type")
#     dest = BRANDING_DIR / f"logo{ext}"
#     dest.write_bytes(await file.read())
#     s = load_settings()
#     url = f"/branding/{dest.name}"
#     s["companyLogoDataUrl"] = url
#     s["logoDataUrl"] = url  # FE alias
#     save_settings(s)
#     return {"ok": True, "url": url}

# ---------- Robots/crawler helpers ----------
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})

def _roboperm(url: str) -> bool:
    from urllib.robotparser import RobotFileParser
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = RobotFileParser()
    try:
        r = SESSION.get(robots_url, timeout=8)
        if r.status_code >= 400:
            return True
        rp.parse(r.text.splitlines())
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True

def _same_origin(a: str, b: str) -> bool:
    pa, pb = urlparse(a), urlparse(b)
    return (pa.scheme, pa.netloc) == (pb.scheme, pb.netloc)

def _extract_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style", "noscript", "template"]):
        t.decompose()
    text = soup.get_text(separator="\n")
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())

def _save_page_text_and_index(request: Request, url: str, text: str) -> str:
    parsed = urlparse(url)
    path_part = (parsed.path or "/").replace("/", "-")
    stem = hyphen_name(f"{parsed.netloc}-{path_part}") or "page"
    fname = f"{stem}.txt"
    out_path = os.path.join(WATCH_DIRECTORY, fname)
    content = f"SOURCE_URL: {url}\n{text}\n"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    # Index immediately
    pages = [{"text": text, "page": 1}]
    if fname in document_ids:
        delete_document_from_db(fname)
    add_document(pages, fname, build_file_url(request, fname, 1))
    return fname

class IngestURLRequest(BaseModel):
    url: str

class IngestSiteRequest(BaseModel):
    start_url: str
    max_pages: int | None = None
    max_depth: int | None = None
    same_origin_only: bool = True
    include_pdfs: bool = False

## MOVED under /api via guarded admin router
# @app.post("/ingest/webpage")
# def ingest_webpage(
#     payload: IngestURLRequest,
#     request: Request,
#     username: str = Depends(require_admin),
# ):
#     url = payload.url.strip()
#     if not re.match(r"^https?://", url):
#         raise HTTPException(status_code=400, detail="URL must start with http(s)://")
#     if not _roboperm(url):
#         raise HTTPException(status_code=403, detail="Robots.txt disallows fetching this URL")
#     r = SESSION.get(url, timeout=20, allow_redirects=True)
#     ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
#     if "text/html" not in ct:
#         raise HTTPException(status_code=415, detail=f"Unsupported content-type: {ct}")
#     text = _extract_text(r.text)
#     name = _save_page_text_and_index(request, url, text)
#     return {"message": "URL ingested", "id": name}
# 
# @app.post("/ingest/website")
# def ingest_website(
#     payload: IngestSiteRequest,
#     request: Request,
#     username: str = Depends(require_admin),
# ):
#     start = payload.start_url.strip()
#     if not re.match(r"^https?://", start):
#         raise HTTPException(status_code=400, detail="start_url must start with http(s)://")
# 
#     max_pages = clamp(payload.max_pages or CRAWL_MAX_PAGES, 1, 1000)
#     max_depth = clamp(payload.max_depth or CRAWL_MAX_DEPTH, 0, 6)
#     same_origin_only = bool(payload.same_origin_only)
#     include_pdfs = bool(payload.include_pdfs)
# 
#     seen: set[str] = set()
#     queue: list[tuple[str, int]] = [(start, 0)]
#     saved: list[str] = []
#     total_bytes = 0
#     origin = start
# 
#     while queue and len(saved) < max_pages:
#         url, depth = queue.pop(0)
#         if url in seen:
#             continue
#         seen.add(url)
#         if same_origin_only and not _same_origin(origin, url):
#             continue
#         if not _roboperm(url):
#             continue
# 
#         try:
#             time.sleep(CRAWL_THROTTLE_SECONDS)
#             resp = SESSION.get(url, timeout=20, allow_redirects=True)
#             ct = resp.headers.get("content-type", "").split(";")[0].strip().lower()
#             total_bytes += len(resp.content)
#             if total_bytes > CRAWL_MAX_TOTAL_BYTES:
#                 break
# 
#             if "text/html" in ct:
#                 html_str = resp.text
#                 text = _extract_text(html_str)
#                 name = _save_page_text_and_index(request, url, text)
#                 saved.append(name)
# 
#                 if depth < max_depth:
#                     soup = BeautifulSoup(html_str, "html.parser")
#                     for a in soup.find_all("a", href=True):
#                         nxt = urljoin(url, a["href"]).split("#", 1)[0]
#                         if nxt.startswith(("mailto:", "javascript:")):
#                             continue
#                         if nxt not in seen and len(seen) + len(queue) < (max_pages * 5):
#                             queue.append((nxt, depth + 1))
# 
#             elif include_pdfs and ct == "application/pdf" and fitz:
#                 name = hyphen_name(Path(urlparse(url).path).name or "file.pdf")
#                 if not name.lower().endswith(".pdf"):
#                     name += ".pdf"
#                 dest = os.path.join(WATCH_DIRECTORY, name)
#                 with open(dest, "wb") as f:
#                     f.write(resp.content)
#                 with open(dest, "rb") as f:
#                     pages = extract_text_from_pdf(f.read())
#                 add_document(pages, name, build_file_url(request, name, 1))
#                 saved.append(name)
# 
#             else:
#                 # ignore other content-types
#                 pass
# 
#         except Exception:
#             continue
# 
#     return {
#         "message": f"Crawl complete: saved {len(saved)} file(s)",
#         "saved": saved,
#         "limits": {
#             "max_pages": max_pages,
#             "max_depth": max_depth,
#             "same_origin_only": same_origin_only,
#             "include_pdfs": include_pdfs,
#         },
#     }

# ---------- Guarded Admin API Router ----------
from app_security import require_admin_basic

# Existing admin router (for backwards compatibility)
admin = APIRouter(prefix="/api", dependencies=[Depends(require_admin_basic)])

# New normalized admin router
admin_normalized = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])

@admin.post("/scan/")
def scan_index():
    scan_directory()
    return {"message": "Directory scanned successfully."}

@admin.post("/upload/")
async def upload_documents(request: Request, files: list[UploadFile] = File(...)):
    uploaded: list[str] = []
    for file in files:
        # Normalize name right away
        name = hyphen_name(file.filename or "file")
        if not _is_supported(name):
            logger.warning(f"Unsupported file type: {name}")
            continue
        dest = os.path.join(WATCH_DIRECTORY, name)

        # Collision-safe target
        if os.path.exists(dest):
            stem, ext = os.path.splitext(name)
            i = 1
            while os.path.exists(os.path.join(WATCH_DIRECTORY, f"{stem}-{i}{ext}")):
                i += 1
            name = f"{stem}-{i}{ext}"
            dest = os.path.join(WATCH_DIRECTORY, name)

        data = await file.read()
        with open(dest, "wb") as f:
            f.write(data)

        ext = Path(name).suffix.lower()
        if ext == ".pdf":
            pages = extract_text_from_pdf(data)
        elif ext in {".txt", ".md"}:
            pages = [{"text": data.decode("utf-8", errors="ignore"), "page": 1}]
        elif ext == ".docx":
            pages = extract_text_from_docx(data)
        elif ext == ".xlsx":
            pages = extract_text_from_xlsx(data)
        elif ext == ".csv":
            pages = extract_text_from_csv(data)
        else:
            continue

        # reindex (delete prior chunks if re-upload)
        if name in document_ids:
            delete_document_from_db(name)

        file_link = build_file_url(request, name, 1)
        add_document(pages, name, file_link)
        uploaded.append(name)

    return {"message": "Documents indexed successfully", "files": uploaded}

@admin.delete("/delete/")
def delete_document(doc_id: str):
    """Soft delete on disk to storage/trash + remove from DB."""
    # Remove from DB first
    delete_document_from_db(doc_id)

    src = os.path.join(WATCH_DIRECTORY, doc_id)
    if not os.path.exists(src):
        return {"message": f"Document '{doc_id}' removed from index (file not on disk)."}

    trash_dir = STORAGE_DIR / "trash"
    trash_dir.mkdir(parents=True, exist_ok=True)
    dst = trash_dir / f"{int(time.time())}_{doc_id}"
    shutil.move(src, dst)
    return {"message": f"Document '{doc_id}' moved to trash and removed from index."}

@admin.post("/reset_memory/")
def reset_memory():
    """Blow away ChromaDB & reinit (does not delete files)."""
    global chroma_client, db_collection, document_ids
    try:
        chroma_client.reset()
        time.sleep(1)
    except Exception:
        pass

    shutil.rmtree(CHROMA_PATH, ignore_errors=True)
    os.makedirs(CHROMA_PATH, exist_ok=True)

    chroma_client = PersistentClient(path=CHROMA_PATH)
    db_collection = chroma_client.get_or_create_collection(name="documents")

    document_ids.clear()
    save_document_ids(document_ids)

    return {"message": "Memory reset successfully."}

@admin.get("/admin/settings")
def get_admin_settings():
    s = load_settings()
    return s

@admin.put("/admin/settings")
def put_settings(payload: dict):
    s = load_settings()
    s.update(payload or {})
    save_settings(s)
    return s

# ---------- Branding (guarded) ----------

# Keys used by the frontend BrandingSettings model
BRANDING_KEYS = {
    # Extended BrandingSettings fields
    "companyName", "logoDataUrl", "faviconUrl",
    "pageBackgroundColor", "pageBackgroundUrl", "chatCardBackgroundColor", 
    "chatCardBackgroundUrl", "inputBackgroundColor",
    "fontFamily", "titleColor", "titleFontSize", "titleBold", "titleItalic",
    "taglineText", "taglineColor", "taglineFontSize", "taglineBold", "taglineItalic",
    "inputTextColor", "inputFontSize", "inputBold", "inputItalic",
    "userBubbleBg", "userTextColor", "userBold", "userItalic",
    "assistantTextColor", "assistantBold", "assistantItalic",
    "sendButtonBgColor", "sendButtonTextColor",
    "glowColor", "glowBlur", "glowSpread", "glowOpacity",
    
    # Legacy compatibility fields
    "primaryColor", "accentColor", "mutedTextColor", "robotLogoDataUrl", "robotSize",
    "emptyStateText", "inputPlaceholder", "fontSize",
    "title", "background", "foreground", "shadow", "robot", "tagline", "emptyState", "placeholder", "favicon",
}

DEFAULT_BRANDING = {
    "title": "LexaAI Company Chatbot",
    "accentColor": "#6bff89",
    "primaryColor": "#FF62DA",
    "mutedTextColor": "#64748b",
    "background": {"color": "#e6eafd"},
    "foreground": {"color": "#0a3a3a"},
    "shadow": {"color": "#6bff89", "blur": 25, "spread": 11, "opacity": 0.15},
    "robot": {"size": 144},  # imageUrl set when logo uploaded
    "tagline": {"fontFamily": "system-ui", "fontSize": 16, "color": "#64748b"},
    "emptyState": {"fontFamily": "system-ui", "fontSize": 14, "color": "#64748b"},
    "placeholder": {"fontFamily": "system-ui", "fontSize": 14, "color": "#9ca3af"},
}

def _get_branding_from_settings(s: dict) -> dict:
    """
    We persist branding inside the same settings blob.
    For back-compat, pull single-value colors from root if present.
    """
    b = dict(DEFAULT_BRANDING)
    # If we already saved a branding sub-object, start from it
    if isinstance(s.get("branding"), dict):
        b.update({k: v for k, v in s["branding"].items() if k in BRANDING_KEYS})

    # Back-compat: map old flat keys if present
    if "primaryColor" in s: b["primaryColor"] = s["primaryColor"]
    if "accentColor"  in s: b["accentColor"]  = s["accentColor"]
    if "mutedTextColor" in s: b["mutedTextColor"] = s["mutedTextColor"]
    if "companyName" in s: b["title"] = s["companyName"]
    if s.get("companyLogoDataUrl"):
        # surface existing logo as the robot image
        b.setdefault("robot", dict(DEFAULT_BRANDING["robot"]))
        b["robot"]["imageUrl"] = s["companyLogoDataUrl"]
    return b

def _apply_branding_to_settings(s: dict, payload: dict) -> dict:
    """Store branding as a sub-object while keeping legacy keys in sync."""
    branding = {k: payload.get(k, DEFAULT_BRANDING[k]) for k in BRANDING_KEYS}
    s["branding"] = branding

    # Keep legacy keys in sync so older UI bits keep working
    s["companyName"]   = branding.get("title", DEFAULT_BRANDING["title"])
    s["primaryColor"]  = branding.get("primaryColor", DEFAULT_BRANDING["primaryColor"])
    s["accentColor"]   = branding.get("accentColor", DEFAULT_BRANDING["accentColor"])
    s["mutedTextColor"]= branding.get("mutedTextColor", DEFAULT_BRANDING["mutedTextColor"])

    # If robot.imageUrl is set, surface it as companyLogoDataUrl for previews
    robot = branding.get("robot") or {}
    if robot.get("imageUrl"):
        s["companyLogoDataUrl"] = robot["imageUrl"]
    return s

@admin.get("/admin/branding")
def get_admin_branding():
    s = load_settings()
    # Return full branding settings with both new and legacy fields for compatibility
    branding_result = _apply_branding_to_public_settings(s)
    
    # Include legacy format fields for backward compatibility, but skip empty URLs
    legacy_data = {
        "title": branding_result.get("companyName"),
        "background": {
            "color": branding_result.get("pageBackgroundColor")
        },
        "foreground": {
            "color": branding_result.get("chatCardBackgroundColor")
        },
        "shadow": {
            "color": branding_result.get("glowColor"),
            "blur": branding_result.get("glowBlur"),
            "spread": branding_result.get("glowSpread"),
            "opacity": branding_result.get("glowOpacity")
        },
        "robot": {
            "imageUrl": branding_result.get("robotLogoDataUrl"),
            "size": branding_result.get("robotSize")
        },
        "tagline": {
            "fontFamily": branding_result.get("fontFamily"),
            "fontSize": branding_result.get("fontSize"),
            "color": branding_result.get("mutedTextColor")
        },
        "emptyState": {
            "fontFamily": branding_result.get("fontFamily"),
            "fontSize": branding_result.get("fontSize") or 14,
            "color": branding_result.get("mutedTextColor")
        },
        "placeholder": {
            "fontFamily": branding_result.get("fontFamily"),
            "fontSize": branding_result.get("fontSize") or 14,
            "color": "#9ca3af"
        }
    }
    
    # Add URL fields only if they're not empty
    page_bg_url = branding_result.get("pageBackgroundUrl")
    if page_bg_url and page_bg_url.strip():
        legacy_data["background"]["imageUrl"] = page_bg_url
        
    chat_bg_url = branding_result.get("chatCardBackgroundUrl") 
    if chat_bg_url and chat_bg_url.strip():
        legacy_data["foreground"]["imageUrl"] = chat_bg_url
    
    branding_result.update(legacy_data)
    
    # Remove None values
    return {k: v for k, v in branding_result.items() if v is not None}

@admin.put("/admin/branding")
def put_admin_branding(payload: dict = Body(...)):
    s = load_settings()
    
    if not payload:
        payload = {}
    
    # Handle both new and legacy formats by merging into settings
    # Legacy format mapping to new keys
    if "title" in payload and "companyName" not in payload:
        payload["companyName"] = payload["title"]
    
    if "background" in payload:
        bg = payload["background"]
        if isinstance(bg, dict):
            if bg.get("color") and "pageBackgroundColor" not in payload:
                payload["pageBackgroundColor"] = bg["color"]
            if bg.get("imageUrl") and "pageBackgroundUrl" not in payload:
                payload["pageBackgroundUrl"] = bg["imageUrl"]
    
    if "foreground" in payload:
        fg = payload["foreground"]
        if isinstance(fg, dict):
            if fg.get("color") and "chatCardBackgroundColor" not in payload:
                payload["chatCardBackgroundColor"] = fg["color"]
            if fg.get("imageUrl") and "chatCardBackgroundUrl" not in payload:
                payload["chatCardBackgroundUrl"] = fg["imageUrl"]
    
    if "shadow" in payload:
        shadow = payload["shadow"]
        if isinstance(shadow, dict):
            if shadow.get("color") and "glowColor" not in payload:
                payload["glowColor"] = shadow["color"]
            if shadow.get("blur") is not None and "glowBlur" not in payload:
                payload["glowBlur"] = shadow["blur"]
            if shadow.get("spread") is not None and "glowSpread" not in payload:
                payload["glowSpread"] = shadow["spread"]
            if shadow.get("opacity") is not None and "glowOpacity" not in payload:
                payload["glowOpacity"] = shadow["opacity"]
    
    if "robot" in payload:
        robot = payload["robot"]
        if isinstance(robot, dict):
            if robot.get("imageUrl") and "robotLogoDataUrl" not in payload:
                payload["robotLogoDataUrl"] = robot["imageUrl"]
            if robot.get("size") is not None and "robotSize" not in payload:
                payload["robotSize"] = robot["size"]
    
    # Map aliases to canonical field names
    if "sendBtnBg" in payload and "sendButtonBgColor" not in payload:
        payload["sendButtonBgColor"] = payload["sendBtnBg"]
    
    if "inputBg" in payload and "inputBackgroundColor" not in payload:
        payload["inputBackgroundColor"] = payload["inputBg"]
    
    # Normalize URL fields: treat "", " none ", and null as null
    def _normalize_url(v):
        if v is None:
            return None
        s = str(v).strip().lower()
        return None if s in ("", "none") else v
    
    # Apply URL normalization and clear from storage when null
    for k in ("pageBackgroundUrl", "chatCardBackgroundUrl"):
        if k in payload:
            payload[k] = _normalize_url(payload[k])
            if payload[k] is None:
                s.pop(k, None)  # Remove from stored settings completely
                # Also clear corresponding legacy fields to prevent fallback
                if k == "pageBackgroundUrl":
                    if "background" in s and isinstance(s["background"], dict):
                        s["background"].pop("imageUrl", None)
                elif k == "chatCardBackgroundUrl":
                    if "foreground" in s and isinstance(s["foreground"], dict):
                        s["foreground"].pop("imageUrl", None)
    
    # Merge all payload into settings
    s.update(payload)
    save_settings(s)
    
    # Return the same format as GET for consistency
    return get_admin_branding()

@admin.post("/admin/branding/logo")
async def upload_logo(
    file: UploadFile | None = File(None),
    url: str | None = Form(None),
):
    s = load_settings()

    # Prefer explicit URL if provided
    if (url or "").strip():
        url = url.strip()
        if not re.match(r"^https?://", url, re.I):
            raise HTTPException(status_code=400, detail="URL must start with http(s)://")
        # No download: just store the remote URL
        s["logoDataUrl"] = url  # Store in canonical key
        save_settings(s)
        return {"ok": True, "url": url, "source": "remote"}

    # Otherwise, fall back to file upload
    if not file:
        raise HTTPException(status_code=400, detail="Provide either 'url' or 'file'")

    ext = Path(file.filename or "").suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    dest = BRANDING_DIR / f"logo{ext}"
    dest.write_bytes(await file.read())

    logo_url = f"/branding/{dest.name}"      # served by StaticFiles mount
    s["logoDataUrl"] = logo_url              # Store in canonical key
    save_settings(s)

    return {"ok": True, "url": logo_url, "source": "upload"}

@admin.post("/admin/assets")
async def upload_asset(file: UploadFile = File(...)):
    """Upload any asset file and return URL for use in branding."""
    ext = Path(file.filename or "").suffix.lower() or ".png"
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico", ".pdf", ".txt"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    # Generate unique filename to avoid collisions
    import time
    timestamp = int(time.time())
    base_name = Path(file.filename or "asset").stem
    dest_name = f"{base_name}_{timestamp}{ext}"
    dest = BRANDING_DIR / dest_name
    
    dest.write_bytes(await file.read())
    asset_url = f"/branding/{dest_name}"
    
    return {"url": asset_url}

@admin.post("/ingest/webpage")
def ingest_webpage(payload: IngestURLRequest, request: Request):
    url = payload.url.strip()
    if not re.match(r"^https?://", url):
        raise HTTPException(status_code=400, detail="URL must start with http(s)://")
    if not _roboperm(url):
        raise HTTPException(status_code=403, detail="Robots.txt disallows fetching this URL")
    r = SESSION.get(url, timeout=20, allow_redirects=True)
    ct = r.headers.get("content-type", "").split(";")[0].strip().lower()
    if "text/html" not in ct:
        raise HTTPException(status_code=415, detail=f"Unsupported content-type: {ct}")
    text = _extract_text(r.text)
    name = _save_page_text_and_index(request, url, text)
    return {"message": "URL ingested", "id": name}

@admin.post("/ingest/website")
def ingest_website(payload: IngestSiteRequest, request: Request):
    start = payload.start_url.strip()
    if not re.match(r"^https?://", start):
        raise HTTPException(status_code=400, detail="start_url must start with http(s)://")

    max_pages = clamp(payload.max_pages or CRAWL_MAX_PAGES, 1, 1000)
    max_depth = clamp(payload.max_depth or CRAWL_MAX_DEPTH, 0, 6)
    same_origin_only = bool(payload.same_origin_only)
    include_pdfs = bool(payload.include_pdfs)

    seen: set[str] = set()
    queue: list[tuple[str, int]] = [(start, 0)]
    saved: list[str] = []
    total_bytes = 0
    origin = start

    while queue and len(saved) < max_pages:
        url, depth = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        if same_origin_only and not _same_origin(origin, url):
            continue
        if not _roboperm(url):
            continue

        try:
            time.sleep(CRAWL_THROTTLE_SECONDS)
            resp = SESSION.get(url, timeout=20, allow_redirects=True)
            ct = resp.headers.get("content-type", "").split(";")[0].strip().lower()
            total_bytes += len(resp.content)
            if total_bytes > CRAWL_MAX_TOTAL_BYTES:
                break

            if "text/html" in ct:
                html_str = resp.text
                text = _extract_text(html_str)
                name = _save_page_text_and_index(request, url, text)
                saved.append(name)

                if depth < max_depth:
                    soup = BeautifulSoup(html_str, "html.parser")
                    for a in soup.find_all("a", href=True):
                        nxt = urljoin(url, a["href"]).split("#", 1)[0]
                        if nxt.startswith(("mailto:", "javascript:")):
                            continue
                        if nxt not in seen and len(seen) + len(queue) < (max_pages * 5):
                            queue.append((nxt, depth + 1))

            elif include_pdfs and ct == "application/pdf" and fitz:
                name = hyphen_name(Path(urlparse(url).path).name or "file.pdf")
                if not name.lower().endswith(".pdf"):
                    name += ".pdf"
                dest = os.path.join(WATCH_DIRECTORY, name)
                with open(dest, "wb") as f:
                    f.write(resp.content)
                with open(dest, "rb") as f:
                    pages = extract_text_from_pdf(f.read())
                add_document(pages, name, build_file_url(request, name, 1))
                saved.append(name)

            else:
                # ignore other content-types
                pass

        except Exception:
            continue

    return {
        "message": f"Crawl complete: saved {len(saved)} file(s)",
        "saved": saved,
        "limits": {
            "max_pages": max_pages,
            "max_depth": max_depth,
            "same_origin_only": same_origin_only,
            "include_pdfs": include_pdfs,
        },
    }

# ---- Normalized Admin Settings (secured) ----

@admin_normalized.get("/settings/branding")
def get_branding_settings_api():
    return extract_branding_fields(load_settings())

@admin_normalized.put("/settings/branding")
def put_branding_settings_api(payload: dict):
    return update_branding_fields(payload)

@admin_normalized.get("/settings/ai")
def get_ai_settings_api():
    return extract_ai_fields(load_settings())

@admin_normalized.put("/settings/ai")
def put_ai_settings_api(payload: dict):
    return update_ai_fields(payload)

@admin_normalized.get("/settings")
def get_full_settings_api():
    return extract_full_settings(load_settings())

@admin_normalized.put("/settings")
def put_full_settings_api(payload: dict):
    return update_full_settings(payload)

# ---- Public Branding (no auth) ----
@app.get("/api/admin/settings/public/branding")
def get_public_branding():
    return extract_branding_fields(load_settings())

app.include_router(admin)
app.include_router(admin_normalized)


