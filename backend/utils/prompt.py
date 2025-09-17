# utils/prompt.py
from typing import Optional, Literal

ResponseStyle = Literal["auto", "paragraphs", "sentences", "bullets", "numbers"]


def style_clause(style: Optional[ResponseStyle]) -> str:
    if style == "paragraphs":
        return "Default format: concise paragraphs. Do not use bullet points unless explicitly asked."
    if style == "sentences":
        return "Answer in 1–3 compact sentences unless the user asks for more detail."
    if style == "bullets":
        return "Default to short bullet points (•), one idea per line."
    if style == "numbers":
        return "Default to a numbered list (1., 2., 3.)."
    return ""


def build_system_prompt(base: str, style: Optional[ResponseStyle]) -> str:
    base = (base or "").strip()
    clause = style_clause(style)
    return f"{base}\n\n{clause}".strip()
