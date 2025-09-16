import os, json, time, threading
from collections import deque

PATH = "data/faq_cache.json"
TTL  = int(os.environ.get("LEXA_FAQ_TTL_SEC", "604800"))  # 7 days
_lock = threading.Lock()
_mem  = None

# Phase 3C Task 2: FAQ Cache Telemetry
faq_hits = 0
faq_misses = 0
_hit_times = deque()  # timestamps of hits in last 60 minutes
_miss_times = deque()  # timestamps of misses in last 60 minutes
WINDOW_SEC = 3600  # 60 minutes

def enabled():
    return os.environ.get("LEXA_USE_FAQ_CACHE","0") == "1"

def _now(): return int(time.time())

def _load():
    global _mem
    if _mem is not None: return
    try:
        with open(PATH, "r") as f:
            _mem = json.load(f)
    except Exception:
        _mem = {}

def _save():
    try:
        os.makedirs("data", exist_ok=True)
        with open(PATH, "w") as f:
            json.dump(_mem, f)
    except Exception:
        pass

def _key(q:str) -> str:
    return (q or "").strip().lower()[:256]

def get(q:str):
    if not enabled(): return None
    global faq_hits, faq_misses
    with _lock:
        _load()
        k = _key(q)
        v = _mem.get(k)
        if not v:
            # Phase 3C Task 2: Track miss
            faq_misses += 1
            _miss_times.append(_now())
            return None
        if _now() - v.get("ts",0) > TTL:
            _mem.pop(k, None)
            _save()
            # Phase 3C Task 2: Track miss (expired)
            faq_misses += 1
            _miss_times.append(_now())
            return None
        # Phase 3C Task 2: Track hit
        faq_hits += 1
        _hit_times.append(_now())
        return v.get("ans")

def set(q:str, ans:str):
    if not enabled(): return
    with _lock:
        _load()
        _mem[_key(q)] = {"ans": ans, "ts": _now()}
        _save()

def _clean_window():
    """Remove timestamps older than WINDOW_SEC from deques"""
    cutoff = _now() - WINDOW_SEC
    while _hit_times and _hit_times[0] < cutoff:
        _hit_times.popleft()
    while _miss_times and _miss_times[0] < cutoff:
        _miss_times.popleft()

def stats():
    """Return FAQ cache statistics"""
    if not enabled():
        return {"enabled": False}
    
    global faq_hits, faq_misses
    with _lock:
        _load()
        entries = len(_mem) if _mem else 0
        
        # Phase 3C Task 2: Clean window and calculate hit rate
        _clean_window()
        hits_last_hour = len(_hit_times)
        misses_last_hour = len(_miss_times)
        total_last_hour = hits_last_hour + misses_last_hour
        hit_rate_1h = hits_last_hour / total_last_hour if total_last_hour > 0 else 0.0
        
        return {
            "enabled": True,
            "entries": entries,
            "file": PATH,
            "ttl_sec": TTL,
            "hits": faq_hits,
            "misses": faq_misses,
            "hit_rate_1h": hit_rate_1h,
            "window_sec": WINDOW_SEC
        }