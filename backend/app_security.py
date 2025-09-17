#!/usr/bin/env python3
# app_security.py
import os
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import HTTPBasic
from fastapi.security import HTTPBasicCredentials

security = HTTPBasic(auto_error=False)

def _env_user() -> str:
    return os.getenv("ADMIN_USER", os.getenv("ADMIN_USERNAME", "admin"))

def _env_pass() -> str:
    return os.getenv("ADMIN_PASSWORD", os.getenv("ADMIN_PASS", "Krypt0n!t3"))

def require_admin_basic(
    request: Request,
    creds: HTTPBasicCredentials | None = Depends(security),
):
    # TEMP DEBUG: prove header arrival + comparison inputs (do NOT log password)
    hdr = request.headers.get("authorization", "")
    scheme = hdr.split(" ", 1)[0].lower() if hdr else ""
    user = creds.username if creds else None

    expected_user = _env_user()
    expected_pass = _env_pass()

    # Normalize to str
    got_user = (user or "").strip()
    exp_user = (expected_user or "").strip()

    ok = bool(creds) and scheme == "basic" and got_user == exp_user and (creds.password or "") == (expected_pass or "")
    
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="Lexa Admin"'}
        )
    return True