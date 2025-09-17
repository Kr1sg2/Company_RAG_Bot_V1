"""
Query rewriting module for NetSuite domain-specific expansion.
Controlled by LEXA_USE_QUERY_REWRITE environment flag.
"""

import os
import re
import logging
from typing import List

logger = logging.getLogger(__name__)

# NetSuite terminology mappings
NETSUITE_SYNONYMS = {
    # Core objects
    "quote": ["quotation", "estimate", "proposal"],
    "sales order": ["SO", "sale order", "order"],
    "opportunity": ["opp", "lead", "prospect"],
    "customer": ["client", "account", "guest"],
    "item": ["product", "inventory", "SKU"],
    # Actions
    "convert": ["change", "transform", "turn into"],
    "create": ["make", "add", "generate", "build"],
    "cancel": ["void", "delete", "remove"],
    "edit": ["modify", "update", "change"],
    # Processes
    "billing": ["invoicing", "charging"],
    "payment": ["deposit", "transaction"],
    "shipping": ["delivery", "fulfillment"],
}

# Process chains - multi-step procedures
PROCESS_CHAINS = {
    "quote to sale": [
        "convert quote to sales order",
        "quote conversion process",
        "sales order from quote",
    ],
    "opportunity to sale": [
        "convert opportunity",
        "close opportunity",
        "opportunity conversion",
    ],
    "customer onboarding": [
        "create customer",
        "customer setup",
        "new customer process",
    ],
    "order fulfillment": ["process sales order", "fulfill order", "shipping process"],
}

# Common abbreviations
ABBREVIATION_EXPANSIONS = {
    "SO": "sales order",
    "PO": "purchase order",
    "NS": "NetSuite",
    "CRM": "customer relationship management",
    "ERP": "enterprise resource planning",
}


def is_enabled() -> bool:
    """Check if query rewriting is enabled via environment flag."""
    return os.getenv("LEXA_USE_QUERY_REWRITE", "false").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def expand_query(original_query: str) -> List[str]:
    """
    Generate expanded query variants for better semantic matching.

    Args:
        original_query: Original user query

    Returns:
        List of query variants including original
    """
    if not is_enabled():
        return [original_query]

    variants = [original_query]
    query_lower = original_query.lower()

    # 1. Add procedural context for how-to queries FIRST so they're not trimmed
    if any(starter in query_lower for starter in ["how to", "how do i", "steps to"]):
        proc1 = query_lower.replace("how to", "steps to")
        if proc1 != query_lower:
            variants.append(proc1)
        proc2 = query_lower.replace("how do i", "process for")
        if proc2 != query_lower:
            variants.append(proc2)
        proc3 = query_lower.replace("how to", "process for")
        if proc3 != query_lower:
            variants.append(proc3)
        # Generic procedure suffix
        if (proc1 != query_lower) or (proc2 != query_lower):
            variants.append(query_lower + " procedure")

    # 2. Abbreviation expansion
    expanded_abbrevs = query_lower
    for abbrev, expansion in ABBREVIATION_EXPANSIONS.items():
        expanded_abbrevs = re.sub(
            r"\b" + re.escape(abbrev.lower()) + r"\b", expansion, expanded_abbrevs
        )
    if expanded_abbrevs != query_lower:
        variants.append(expanded_abbrevs)

    # 3. Synonym expansion (limited)
    for term, synonyms in NETSUITE_SYNONYMS.items():
        if term in query_lower:
            for synonym in synonyms[
                :1
            ]:  # Limit to 1 synonym per term to avoid explosion
                synonym_variant = query_lower.replace(term, synonym)
                if synonym_variant != query_lower:
                    variants.append(synonym_variant)

    # 4. Process chain detection (require at least two words to match)
    for process, expansions in PROCESS_CHAINS.items():
        words = set(process.split())
        match_count = sum(1 for w in words if w in query_lower)
        if process in query_lower or match_count >= 2:
            variants.extend(expansions)

    # Remove duplicates and limit variants
    # Preserve insertion order and keep to max 5 total variants
    unique_variants = list(dict.fromkeys(variants))[:5]

    if len(unique_variants) > 1:
        logger.info(
            f"Query expanded: '{original_query}' → {len(unique_variants)} variants"
        )

    return unique_variants


def get_query_intent(query: str) -> str:
    """
    Classify query intent for different retrieval strategies.

    Returns: 'procedural', 'factual', 'troubleshooting', 'navigation'
    """
    query_lower = query.lower()

    # Troubleshooting queries - check FIRST to catch phrasing like "how to fix"
    if any(
        issue in query_lower
        for issue in [
            "error",
            "problem",
            "issue",
            "not working",
            "failed",
            "wrong",
            "missing",
            "broken",
            "fix",
        ]
    ):
        return "troubleshooting"

    # Procedural queries
    if any(
        starter in query_lower
        for starter in [
            "how to",
            "how do i",
            "steps to",
            "process for",
            "way to",
            "create",
            "make",
            "convert",
            "cancel",
            "setup",
        ]
    ):
        return "procedural"

    # Navigation queries
    if any(
        nav in query_lower
        for nav in ["where is", "where do i find", "locate", "menu", "button", "page"]
    ):
        return "navigation"

    # Default to factual
    return "factual"
