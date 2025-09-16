# Robust shim:
# - Flattens nested metadata to dot keys
# - Injects pipeline="pipeline_fixed" if missing
# - Heuristically sets chunk_type if missing (faq|procedure|form|passage)
# - Patches both our DocumentStore and Chroma Collection.add/upsert

def _flatten_meta(d, prefix=""):
    out={}
    if not isinstance(d, dict): return out
    for k,v in d.items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            out.update(_flatten_meta(v, key))
        elif isinstance(v, (list, tuple, set)):
            out[key] = ", ".join(map(str, v))
        else:
            out[key] = v
    return out

def _infer_chunk_type(text, meta):
    t = (text or "")
    t = t.lower() if isinstance(t, str) else ""
    name = (meta or {}).get("file_name","").lower()
    hpth = (meta or {}).get("h_path","").lower()
    if "q&a" in t or "faq" in t or t.startswith("q:") or "faq" in name or "faq" in hpth: return "faq"
    if "procedure" in t or "step " in t or "steps:" in t or "how to" in t or "procedure" in hpth: return "procedure"
    if "form" in t or "form" in name: return "form"
    return "passage"

def _inject_defaults(d, text=None):
    d = dict(d or {})
    d.setdefault("pipeline", "pipeline_fixed")
    d.setdefault("chunk_type", _infer_chunk_type(text, d))
    return d

def _wrap_on(cls, method, has_chunks=False):
    import functools
    orig = getattr(cls, method, None)
    if not callable(orig): return False
    @functools.wraps(orig)
    def wrapper(*args, **kwargs):
        # Case: add/upsert(documents=..., metadatas=[...])
        if "metadatas" in kwargs and isinstance(kwargs["metadatas"], list):
            docs = kwargs.get("documents") or []
            new_metas=[]
            for i,m in enumerate(kwargs["metadatas"]):
                mi = _inject_defaults(m, (docs[i] if i < len(docs) else None))
                new_metas.append(_flatten_meta(mi))
            kwargs["metadatas"] = new_metas
        # Case: chunks=[{"text":..., "metadata": {...}}, ...]
        if has_chunks and "chunks" in kwargs and isinstance(kwargs["chunks"], list):
            chs=[]
            for ch in kwargs["chunks"]:
                if isinstance(ch, dict):
                    meta = ch.get("metadata") or {}
                    txt  = ch.get("text")
                    meta = _inject_defaults(meta, txt)
                    meta = _flatten_meta(meta)
                    ch   = dict(ch, metadata=meta)
                chs.append(ch)
            kwargs["chunks"] = chs
        return orig(*args, **kwargs)
    setattr(cls, method, wrapper); return True

# Patch our store
try:
    from . import store as _store
    for cls_name in ("DocumentStore","Store"):
        C = getattr(_store, cls_name, None)
        if C:
            for m in ("add_documents","upsert_documents"): _wrap_on(C, m, has_chunks=False)
            for m in ("add_chunks","upsert_chunks"):       _wrap_on(C, m, has_chunks=True)
except Exception:
    pass

# Patch Chroma Collection as safety net
try:
    from chromadb.api.models import Collection as _cmod  # chromadb>=0.4
    _C=_cmod.Collection
    for m in ("add","upsert"): _wrap_on(_C, m, has_chunks=False)
except Exception:
    pass
