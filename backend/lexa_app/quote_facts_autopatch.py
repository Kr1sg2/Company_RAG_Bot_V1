# lexa_app/quote_facts_autopatch.py
import os
import re

NUM_RX = re.compile(r'(?i)(\b\$?\d{1,4}(?:[.,]\d{3})*(?:\.\d+)?\b)\s*(days?|months?|years?|usd|\$|percent|%)')
TRIGGER_RX = re.compile(r'(?i)how\s+long|days?|months?|years?|limit|price|cap|approval|eligible|eligibility|tenure|employment')

def _get_text(c):
    if isinstance(c, dict):
        return c.get("text") or c.get("document") or c.get("content") or c.get("page_content") or ""
    return str(c or "")

def _meta(c):
    m = (c.get("metadata") or c.get("metadatas") or {})
    if isinstance(m, list) and m:
        m = m[0]
    return m or {}

def _name(m):
    return m.get("file_name") or m.get("source") or m.get("doc_name") or "source"
def _page(m):
    for k in ("page", "page_start", "page_no", "page_number"):
        if k in m:
            try:
                return int(m[k])
            except Exception:
                pass
    return None

def _sentences(t):
    # crude but robust sentence split
    return re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])', t or "")

def _find_fact_sentence(text):
    best = None
    for s in _sentences(text):
        if NUM_RX.search(s):
            best = s.strip()
            break
    return best

def apply_patch(globs: dict) -> bool:
    if os.getenv("LEXA_QUOTE_FACTS","1") not in ("1","true","TRUE","yes"):
        return False

    # find route and retriever
    target, orig = None, None
    for k in ("chat", "api_chat", "chat_api", "chat_route", "respond", "answer"):
        fn = globs.get(k)
        if callable(fn):
            target, orig = k, fn
            break
    if not target: return False

    retr = None
    for name in ("retrieve", "retrieve_chunks", "search_chunks", "search", "get_context"):
        fn = globs.get(name)
        if callable(fn):
            retr = fn
            break

    if not retr: 
        return False

    def wrapped(*args, **kwargs):
        out = orig(*args, **kwargs)
        try:
            query = kwargs.get("query") or (args[0] if args else "") or ""
            if not TRIGGER_RX.search(str(query)):
                return out

            # pull a wider pool and scan for numeric sentence
            cands = retr(str(query), k=int(os.getenv("LEXA_K_MAX", "18")))
            if not isinstance(cands, list): 
                return out

            fact = None
            meta = None
            for c in cands:
                t = _get_text(c)
                s = _find_fact_sentence(t)
                if s:
                    fact = s
                    meta = _meta(c)
                    break

            if not fact:
                return out

            # normalize resp fields
            if isinstance(out, dict):
                resp = out.get("response") or out.get("answer") or ""
                prepend = (
                    f"Direct quote from {_name(meta)} (p.{_page(meta)}): \"{fact}\"\n\n"
                )
                out["response"] = prepend + (resp or "")
                # raise confidence floor when quoting directly from source
                try:
                    if float(out.get("confidence", 0)) < 0.62:
                        out["confidence"] = 0.62
                        out["confidence_rationale"] = "Contains direct numeric quote from source."
                except Exception:
                    out["confidence"] = 0.62
                    out["confidence_rationale"] = "Contains direct numeric quote from source."
            return out
        except Exception:
            return out

    globs[target] = wrapped
    globs["_quote_facts_patched"] = target
    return True
