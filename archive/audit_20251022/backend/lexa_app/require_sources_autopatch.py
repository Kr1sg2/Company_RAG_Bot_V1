# lexa_app/require_sources_autopatch.py
import os
from typing import Any, Dict

_MIN = int(os.getenv("LEXA_MIN_SOURCES", "1"))
_MSG = os.getenv("LEXA_NO_SOURCE_MESSAGE",
                 "I couldn't find a grounded answer in the indexed documents.")
_ON  = os.getenv("LEXA_REQUIRE_SOURCES", "1").lower() in ("1","true","yes")

_KEYS = ("chat","api_chat","chat_api","chat_route","answer","qa","respond")

def _looks_like_resp(x: Any) -> bool:
    return isinstance(x, dict) and ("response" in x or "answer" in x)

def _normalize(resp: Dict[str,Any]) -> Dict[str,Any]:
    # prefer "response"; keep both if they already exist
    if "response" not in resp and "answer" in resp:
        resp["response"] = resp.get("answer")
    if "sources" not in resp or resp["sources"] is None:
        resp["sources"] = []
    return resp

def apply_patch(globs: dict) -> bool:
    if not _ON:
        return False
    # find a route-like function we can wrap (works at app layer)
    target_name, orig = None, None
    for name in _KEYS:
        fn = globs.get(name)
        if callable(fn):
            target_name, orig = name, fn
            break
    if not target_name:
        return False

    def wrapped(*args, **kwargs):
        out = orig(*args, **kwargs)
        try:
            if not _looks_like_resp(out):
                return out
            out = _normalize(out)
            srcs = out.get("sources") or []
            if len(srcs) >= _MIN:
                return out
            # Not enough sources → return grounded "no answer"
            return {
                "response": _MSG,
                "sources": [],
                "confidence": 0.0,
                "confidence_rationale": "No supporting sources retrieved.",
                "cache_hit": False,
            }
        except Exception:
            # Fail open: never break your API
            return out

    globs[target_name] = wrapped
    globs["_require_sources_patched"] = target_name
    return True
