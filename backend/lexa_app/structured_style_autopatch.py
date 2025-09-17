# lexa_app/structured_style_autopatch.py
import os

GUIDE = """You are answering questions about internal company documents.
When possible, produce a structured answer with these sections (omit ones you can't justify from sources):
- Direct answer (1–2 sentences)
- Requirements (bullets: approvals, limits, forms)
- Process steps (numbered, concrete verbs)
- Timeline (durations & SLAs)
- Exceptions (edge cases / not permitted)
- Related policies (titles from sources)
Keep it concise and grounded in the retrieved text. Do not invent policy or amounts you cannot cite."""

def _inject(style, out):
    # String prompt
    if isinstance(out, str):
        return style + "\n\n" + out
    # Dict-like {system,user} or {messages:[...]}
    if isinstance(out, dict):
        o = dict(out)
        if "system" in o and isinstance(o["system"], str):
            o["system"] = style + "\n\n" + o["system"]
        elif "messages" in o and isinstance(o["messages"], list):
            # Prepend a system message if not present
            msgs = list(o["messages"])
            if not msgs or msgs[0].get("role") != "system":
                msgs.insert(0, {"role":"system","content":style})
            else:
                msgs[0]["content"] = style + "\n\n" + (msgs[0].get("content") or "")
            o["messages"] = msgs
        return o
    return out

def apply_patch(globs: dict) -> bool:
    if os.getenv("LEXA_STRUCTURED", "1") not in ("1", "true", "TRUE", "yes"):
        return False
    target_name, orig = None, None
    # Common prompt-builder names to wrap
    for name in ("build_prompt","compose_prompt","make_prompt","create_prompt","format_prompt"):
        fn = globs.get(name)
        if callable(fn):
            target_name, orig = name, fn
            break
    if not orig:
        return False

    def wrapped(*args, **kwargs):
        out = orig(*args, **kwargs)
        return _inject(GUIDE, out)

    globs[target_name] = wrapped
    globs["_structured_patched"] = target_name
    return True
