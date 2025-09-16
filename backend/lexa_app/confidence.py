import os, math, re

def enabled():
    return os.environ.get("LEXA_USE_CONFIDENCE","0") == "1"

def _sigmoid(x): return 1.0/(1.0+math.exp(-x))

def estimate_citations(text:str)->int:
    if not text: return 0
    # Count URLs and bracketed references
    urls = len(re.findall(r'https?://\S+', text))
    brackets = len(re.findall(r'\[\d+\]|\[[^\]]+\]', text))
    return urls + brackets

def score(struct:int, cites:int, disagree:float=0.0)->float:
    s = 0.45*_sigmoid(struct-1) + 0.35*_sigmoid(cites-1) + 0.20*(1.0 - max(0.0, min(disagree,1.0)))
    return round(max(0.0, min(1.0, s)), 3)