# lexa_app/hybrid_autopatch.py
import math
import os
import re
from collections import Counter

# ---------- tiny helpers ----------
_WORD = re.compile(r"[a-z0-9]+")

def _tok(s: str):
    return _WORD.findall((s or "").lower())

_SYNONYMS = {
    "policy": ["procedure","guidelines","rules","standard"],
    "purchase": ["buy","procure","acquire","order"],
    "approval": ["authorize","sign off","sign-off","approve"],
    "eligible": ["qualification","qualify","eligibility","who can"],
    "pricing": ["price","cost","amount","limit","cap","maximum"],
        "laptop": ["computer","notebook","device","hardware"],
        "program": ["plan","policy","scheme"],
        "purchase program": ["buying program","procurement program","laptop plan","employee laptop plan"],
    "employee center": ["employees center","netsuite employee center","suite","portal"],
}

def _expand_queries(q: str, limit: int = 5):
    ql = q.lower()
    ex = {q}
    # noun-phrase quotes
    for m in re.findall(r'"([^"]+)"|(\w+\s+\w+)', q):
        phrase = (m[0] or m[1] or "").strip()
        if phrase and " " in phrase:
            ex.add(f'"{phrase}"')
    # synonym bumps
    for k, syns in _SYNONYMS.items():
        if k in ql:
            for s in syns:
                ex.add(ql.replace(k, s))
    # decompositions (simple)
    if " and " in ql:
        a, b = ql.split(" and ", 1)
        ex.update({a.strip(), b.strip()})
    return list(ex)[:1+limit]

def _idf(corpus_tokens):
    N = len(corpus_tokens)
    df = Counter()
    for doc in corpus_tokens:
        df.update(set(doc))
    return {t: math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5)) for t in df}

PRESENCE_BONUS = {
    'approval': 0.15,
    'limit': 0.15,
    'pricing': 0.15,
    'price': 0.15,
    'eligible': 0.10,
}
def _bm25(qtoks, dtoks, idf, avgdl, k1=1.2, b=0.75):
    if not dtoks:
        return 0.0
    freq = Counter(dtoks)
    score = 0.0
    dl = len(dtoks)
    for t in qtoks:
        if t not in idf or t not in freq:
            continue
        tf = freq[t]
        denom = tf + k1 * (1 - b + b * dl / (avgdl or 1))
        score += idf[t] * (tf * (k1 + 1) / (denom or 1))
    return score

def _norm(xs):
    if not xs:
        return xs
    m, M = min(xs), max(xs)
    if M <= m:
        return [0.0] * len(xs)
    return [(x - m) / (M - m) for x in xs]

def _get_text(c):
    if isinstance(c, dict):
        return c.get("text") or c.get("document") or c.get("content") or c.get("page_content") or ""
    return str(c)

def _get_vecscore(c):
    # try several common keys; higher is better
    if isinstance(c, dict):
        if "similarity" in c:
            return float(c["similarity"])
        if "score" in c:
            return float(c["score"])
        if "distance" in c:
            return 1.0 - float(c["distance"])
    return 0.0

# ---------- public: fuse + rerank ----------
TABLE_BONUS=0.12
LIMIT_TERMS=('price','pricing','cost','limit','cap','approval','approve','authorized','table','tenure','employment','eligible','eligibility','wait','waiting','days','months','years')
NUM_BONUS = float(os.getenv('LEXA_NUM_BONUS', '0.18'))
NUM_RX = re.compile(r'(?i)(\b\$?\d{1,4}(?:[.,]\d{3})*(?:\.\d+)?\b)\s*(days?|months?|years?|usd|\$|percent|%)')
NEAR_RX = re.compile(r'(?i)(eligible|eligibility|tenure|employment|approval|limit|price|pricing|cap|cost|wait|since|after)')

def _has_num_context(t):
    t = t or ''
    if not NUM_RX.search(t):
        return False
    # look within ~100 chars of a policy term
    for m in NEAR_RX.finditer(t):
        a, b = max(0, m.start() - 100), m.end() + 100
        if NUM_RX.search(t[a:b]):
            return True
    return False

def hybrid_rerank(query, candidates, k=None):
    ql=(query or '').lower()
    bonus=sum(v for k,v in PRESENCE_BONUS.items() if k in ql)
    """Rerank a list of candidate chunks (dicts or strings) using BM25-like lexical
    scoring over *expanded queries*, then fuse with vector score."""
    if not candidates:
        return candidates
    w = float(os.getenv("LEXA_FUSE_WEIGHT", "0.65"))  # weight for vector side
    expand_n = int(os.getenv("LEXA_EXPAND_N", "4"))
    exqs = _expand_queries(query, limit=expand_n)
    # tokenise docs once
    dtoks = [_tok(_get_text(c)) for c in candidates]
    idf = _idf(dtoks)
    avgdl = sum(map(len, dtoks)) / (len(dtoks) or 1)
    # best lexical score per doc across all expansions
    lex = []
    for d in dtoks:
        best = 0.0
        for qx in exqs:
            best = max(best, _bm25(_tok(qx), d, idf, avgdl))
        lex.append(best)
    # fuse
    vec = [_get_vecscore(c) for c in candidates]
    L, V = _norm(lex), _norm(vec)
    ql = (query or '').lower()
    tbl_hint = any(t in ql for t in LIMIT_TERMS)
    # attach scores & sort
    out = []
    for i, c in enumerate(candidates):
        t = _get_text(c).lower()
        has_tbl = ('|') in t or 'table' in t or 'column' in t  # crude but effective
    bonus_tbl = TABLE_BONUS if tbl_hint and has_tbl else 0.0
    bonus_num = NUM_BONUS if _has_num_context(t) else 0.0
        fused_score = w*V[i] + (1-w)*(L[i]+bonus) + bonus_tbl + bonus_num
        if isinstance(c, dict):
            c = dict(c)
            c.setdefault("metrics", {})
            c["metrics"].update({"lex": L[i], "vec": V[i], "fused": fused_score, "has_num": 1 if bonus_num>0 else 0})
        out.append((fused_score, c))
    out.sort(key=lambda x: x[0], reverse=True)
    ranked = [c for _, c in out]
    # DIVERSITY_ON
    if os.getenv('LEXA_DIVERSITY', '1') in ('1', 'true', 'TRUE', 'yes'):
        max_per = int(os.getenv('LEXA_DUP_MAX_PER_PAGE','2'))   # max chunks per (doc,page)
        thr = float(os.getenv('LEXA_NEAR_DUP_JACCARD','0.88'))  # 0..1 (higher = stricter dedup)

        def _meta(c):
            m = (c.get('metadata') or c.get('metadatas') or {})
            if isinstance(m, list) and m: m = m[0]
            return m or {}
        def _page(m):
            for k in ('page', 'page_start', 'page_no', 'page_number'):
                if k in m:
                    try:
                        return int(m[k])
                    except Exception:
                        pass
            return None
        def _name(m):
            return m.get('file_name') or m.get('source') or m.get('doc_name')
        def _sig(c):
            return set(_tok(_get_text(c)))

        selected = []
        seen = {}  # (name,page) -> count
        for c in ranked:
            m = _meta(c)
            key = (_name(m), _page(m))
            seen[key] = seen.get(key, 0)

            if seen[key] >= max_per:
                continue

            sig = _sig(c)
            is_dup = False
            for sc in selected:
                ssig = sc.get('__sig')
                if not sig or not ssig:
                    continue
                inter = len(sig & ssig)
                uni = len(sig | ssig) or 1
                if inter / uni >= thr:
                    is_dup = True
                    break
            if is_dup:
                continue

            if isinstance(c, dict):
                c = dict(c)
                c['__sig'] = sig
            selected.append(c)
            seen[key] += 1
            if len(selected) >= (k or len(ranked)):
                break

        ranked = [{k:v for k,v in c.items() if k != '__sig'} if isinstance(c,dict) else c for c in selected]

    return ranked[:k] if k else ranked

def apply_patch(globs: dict) -> bool:
    """Monkey-patch the first retriever function we can find."""
    if os.getenv("LEXA_HYBRID", "1") not in ("1", "true", "TRUE", "yes"):
        return False
    target = None
    for name in ("retrieve", "retrieve_chunks", "search_chunks", "search", "get_context"):
        fn = globs.get(name)
        if callable(fn):
            target = name
            orig = fn
            break
    if not target: 
        return False

    def wrapped(query, *args, **kwargs):
        # try to read desired k; bump internal k for more candidates
        k = kwargs.get("k")
        if k is None and len(args) > 0 and isinstance(args[0], int):
            k = args[0]
        k = int(k or int(os.getenv("LEXA_K_DEFAULT", "12")))
        bigk = max(k, int(os.getenv("LEXA_K_MAX", "18")))
        # call original with a larger k to get a wider pool
        if len(args) > 0 and isinstance(args[0], int):
            args = (bigk,) + tuple(args[1:])
            kw = dict(kwargs)
        else:
            kw = dict(kwargs)
            kw["k"] = bigk
        cands = orig(query, *args, **kw)
        try:
            return hybrid_rerank(query, cands, k=k)
        except Exception:
            return cands[:k]
    globs[target] = wrapped
    globs["_hybrid_patched"] = target
    return True