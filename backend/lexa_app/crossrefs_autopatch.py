# lexa_app/crossrefs_autopatch.py
import os
import re

_REF_PATTERNS = [
    re.compile(r'\b(see|refer to)\s+(section|sec\.?)\s+([0-9][0-9.\-]*)', re.I),
    re.compile(r'\b(see|refer to)\s+page\s+([0-9]{1,3})', re.I),
    re.compile(r'\b(see|refer to)\s+(appendix|table)\s+([A-Z0-9\-]+)', re.I),
]

def _get_text(c):
    if isinstance(c, dict):
        return c.get("text") or c.get("document") or c.get("content") or c.get("page_content") or ""
    return str(c or "")

def _get_name(c):
    if isinstance(c, dict):
        m = c.get("metadata") or c.get("metadatas") or {}
        if isinstance(m, list) and m:
            m = m[0]
        return (m or {}).get("file_name") or (m or {}).get("source") or (m or {}).get("doc_name")
    return None

def _score(c):
    if isinstance(c, dict):
        m = c.get("metrics") or {}
        if "fused" in m:
            return float(m["fused"])
        if "score" in c:
            return float(c["score"])
        if "similarity" in c:
            return float(c["similarity"])
        if "distance" in c:
            return 1.0 - float(c["distance"])
    return 0.0

def _extract_refs(text, max_refs=3):
    refs = []
    t = text or ""
    for rx in _REF_PATTERNS:
        for m in rx.finditer(t):
            chunk = m.group(0)
            # keep short, queryable phrases
            if 4 <= len(chunk) <= 80:
                refs.append(chunk)
                if len(refs) >= max_refs:
                    return refs
    return refs

def apply_patch(globs: dict) -> bool:
    if os.getenv("LEXA_CROSSREFS","1") not in ("1","true","TRUE","yes"):
        return False

    # find an existing retriever (possibly already hybrid-wrapped)
    target = None
    for name in ("retrieve", "retrieve_chunks", "search_chunks", "search", "get_context"):
        fn = globs.get(name)
        if callable(fn):
            target, orig = name, fn
            break
    if not target:
        return False

    def wrapped(query, *args, **kwargs):
        # determine k/bigk like our other wrappers
        k = kwargs.get("k")
        if k is None and len(args) > 0 and isinstance(args[0], int):
            k = args[0]
        k = int(k or int(os.getenv("LEXA_K_DEFAULT","12")))
        bigk = max(k, int(os.getenv("LEXA_K_MAX","18")))
        # initial candidates
        kw = dict(kwargs)
        if len(args) > 0 and isinstance(args[0], int):
            args2 = (bigk,) + tuple(args[1:])
        else:
            args2, kw = tuple(args), dict(kwargs)
            kw["k"] = bigk
        cands = orig(query, *args2, **kw)

        # cross-ref harvest from top docs
        if not isinstance(cands, list) or not cands:
            return cands
        max_refs = int(os.getenv("LEXA_CROSSREFS_LIMIT","2"))
        per_ref_pull = int(os.getenv("LEXA_CROSSREFS_PER_REF","2"))

        # restrict to same docs as top candidates
        top_names = []
        for c in cands[:6]:
            n = _get_name(c)
            if n and n not in top_names:
                top_names.append(n)

        extras = []
        seen_ids = set()
        def _cid(x):
            if isinstance(x, dict):
                return x.get("id") or x.get("ids") or ( _get_name(x), _get_text(x)[:64] )
            return id(x)

        for c in cands[:6]:
            refs = _extract_refs(_get_text(c), max_refs=max_refs)
            base_doc = _get_name(c)
            for r in refs:
                # pull a few hits for the reference phrase, prefer same document
                pulls = orig(r, **{"k": per_ref_pull})
                for p in pulls or []:
                    if base_doc and _get_name(p) and _get_name(p) != base_doc: 
                        continue
                    cid = _cid(p)
                    if cid in seen_ids: 
                        continue
                    seen_ids.add(cid)
                    extras.append(p)

        # combine and rerank by available score fields
        pool = cands + extras
        pool.sort(key=_score, reverse=True)
        return pool[:k]

    globs[target] = wrapped
    globs["_crossrefs_patched"] = target
    return True
