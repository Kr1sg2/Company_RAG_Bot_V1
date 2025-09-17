"""
Section detection rules and patterns for smart document chunking.
"""

import re
from typing import Dict, List, Optional, Tuple

# Chunk size configuration
CHUNK_MIN_CHARS = 180
CHUNK_MAX_CHARS = 1100
OVERLAP_TOKENS = 80
MERGE_NEARBY = True

# Common structural patterns
STEP_RX = re.compile(r"^\s*(?:step\s*)?\d+[\.\):]\s+", re.IGNORECASE)
BULLET_RX = re.compile(r"^\s*[•\-\*]\s+")
WARNING_RX = re.compile(r"\b(?:DO NOT|WARNING|CAUTION|IMPORTANT|NOTE)\b", re.IGNORECASE)
CROSS_REF_RX = re.compile(r"see page (\d+)", re.IGNORECASE)
SUPPLY_HEADING_RX = re.compile(
    r"^\s*(?:supplies|materials|you will need|tools required)[:.]?\s*$", re.IGNORECASE
)

# Section heading patterns
ROMAN_NUMERAL_RX = re.compile(r"^\s*[IVX]+\.\s+")
LETTER_SECTION_RX = re.compile(r"^\s*[A-Z]\.\s+")
NUMBER_SECTION_RX = re.compile(r"^\s*\d+\.\s+")
SUBSECTION_RX = re.compile(r"^\s*\d+\.\d+\s+")

# Document type categorization patterns
PRODUCT_CARE_PATTERNS = {
    "keywords": [
        "quick fix",
        "rattan",
        "white wicker",
        "blush spray",
        "lemon oil",
        "cleaning",
        "maintenance",
        "touch up",
        "repair",
        "scratch",
    ],
    "section_headers": ["rattan", "wicker", "aluminum", "fabric", "cushions", "frames"],
}

NETSUITE_PATTERNS = {
    "keywords": [
        "login",
        "navigate to",
        "dashboard",
        "field:",
        "netsuite",
        "sales order",
        "customer",
        "inventory",
        "billing",
        "account",
        "screen",
        "tab",
    ],
    "section_headers": ["procedure", "steps", "navigation", "process"],
}

POLICY_PATTERNS = {
    "keywords": [
        "policy",
        "scope",
        "effective date",
        "procedure",
        "guidelines",
        "employee",
        "benefits",
        "pto",
        "vacation",
        "discipline",
    ],
    "section_headers": ["purpose", "scope", "policy", "procedure", "definitions"],
}

FORM_PATTERNS = {
    "keywords": [
        "form",
        "request",
        "submit",
        "application",
        "fill out",
        "complete",
        "signature",
        "date",
        "print name",
    ],
    "indicators": ["___", "[ ]", "checkbox", "fill in", "sign here"],
}


def detect_document_category(text: str, doc_type: str = None) -> str:
    """Detect document category from text content."""
    text_lower = text.lower()

    # Use Phase 1 classification if available
    if doc_type:
        if doc_type == "netsuite_guide":
            return "netsuite_guide"
        elif doc_type == "business_process":
            return "policy"
        elif doc_type == "form":
            return "form"
        elif doc_type == "user_manual":
            return "product_care"

    # Fallback to content-based detection
    scores = {
        "product_care": sum(
            1 for kw in PRODUCT_CARE_PATTERNS["keywords"] if kw in text_lower
        ),
        "netsuite_guide": sum(
            1 for kw in NETSUITE_PATTERNS["keywords"] if kw in text_lower
        ),
        "policy": sum(1 for kw in POLICY_PATTERNS["keywords"] if kw in text_lower),
        "form": sum(1 for kw in FORM_PATTERNS["keywords"] if kw in text_lower),
    }

    return max(scores, key=scores.get) if max(scores.values()) > 0 else "general"


def extract_step_info(text: str) -> Optional[Dict]:
    """Extract step number and procedure info from text."""
    match = STEP_RX.match(text.strip())
    if match:
        step_line = text.split("\n")[0]
        step_num_match = re.search(r"\d+", step_line)
        step_num = int(step_num_match.group()) if step_num_match else None
        return {
            "step_number": step_num,
            "step_line": step_line.strip(),
            "is_step": True,
        }
    return None


def detect_section_headers(text: str) -> List[Tuple[str, int, str]]:
    """Detect section headers and their types."""
    headers = []
    lines = text.split("\n")

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Check different header patterns
        if ROMAN_NUMERAL_RX.match(line_stripped):
            headers.append((line_stripped, i, "roman"))
        elif LETTER_SECTION_RX.match(line_stripped):
            headers.append((line_stripped, i, "letter"))
        elif NUMBER_SECTION_RX.match(line_stripped):
            headers.append((line_stripped, i, "numbered"))
        elif SUBSECTION_RX.match(line_stripped):
            headers.append((line_stripped, i, "subsection"))
        elif (
            len(line_stripped) < 80
            and line_stripped.isupper()
            and len(line_stripped) > 5
        ):
            headers.append((line_stripped, i, "caps"))

    return headers


def extract_warnings_and_notes(text: str) -> List[str]:
    """Extract warning and note sections."""
    warnings = []
    for match in WARNING_RX.finditer(text):
        # Get the sentence containing the warning
        start = text.rfind(".", 0, match.start()) + 1
        end = text.find(".", match.end())
        if end == -1:
            end = len(text)
        warning_text = text[start:end].strip()
        if warning_text:
            warnings.append(warning_text)
    return warnings


def extract_cross_references(text: str) -> List[Dict]:
    """Extract cross-references to other pages/sections."""
    refs = []
    for match in CROSS_REF_RX.finditer(text):
        refs.append(
            {
                "page": int(match.group(1)),
                "context": text[max(0, match.start() - 50) : match.end() + 50].strip(),
            }
        )
    return refs


def extract_supply_lists(text: str) -> List[str]:
    """Extract supply/materials lists."""
    supplies = []
    lines = text.split("\n")

    in_supply_section = False
    for line in lines:
        line_stripped = line.strip()

        if SUPPLY_HEADING_RX.match(line_stripped):
            in_supply_section = True
            continue

        if in_supply_section:
            if BULLET_RX.match(line_stripped) or line_stripped.startswith("-"):
                supply_item = BULLET_RX.sub("", line_stripped).strip()
                if supply_item:
                    supplies.append(supply_item)
            elif (
                line_stripped == ""
                or ROMAN_NUMERAL_RX.match(line_stripped)
                or LETTER_SECTION_RX.match(line_stripped)
                or NUMBER_SECTION_RX.match(line_stripped)
                or SUBSECTION_RX.match(line_stripped)
                or (line_stripped.isupper() and len(line_stripped) > 5)
            ):
                in_supply_section = False

    return supplies


def detect_form_fields(text: str) -> Dict:
    """Detect form-like structures and field groups."""
    form_indicators = sum(
        1 for pattern in FORM_PATTERNS["indicators"] if pattern in text
    )

    # Look for field-like patterns
    field_patterns = [
        r"_+",  # Blank lines
        r"Date:\s*_+",
        r"Name:\s*_+",
        r"Signature:\s*_+",
        r"\[\s*\]",  # Checkboxes
    ]

    field_count = sum(
        len(re.findall(pattern, text, re.IGNORECASE)) for pattern in field_patterns
    )

    return {
        "has_form_fields": field_count > 2 or form_indicators > 1,
        "field_count": field_count,
        "form_indicators": form_indicators,
    }
