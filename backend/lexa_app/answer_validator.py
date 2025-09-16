"""
Answer validation module to ensure response quality.
Controlled by LEXA_USE_ANSWER_VALIDATION environment flag.
"""
import os
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

def is_enabled() -> bool:
    """Check if answer validation is enabled via environment flag."""
    return os.getenv("LEXA_USE_ANSWER_VALIDATION", "false").lower() in ("1", "true", "yes", "on")

def count_steps(text: str) -> int:
    """
    Count numbered or bulleted steps in answer text.
    
    Args:
        text: Answer text to analyze
        
    Returns:
        Number of steps found
    """
    # Pattern 1: Numbered lists (1. 2. 3. or 1) 2) 3))
    numbered_steps = len(re.findall(r'^\s*\d+[\.\)]\s+', text, re.MULTILINE))
    
    # Pattern 2: Bullet points (- * •)
    bullet_steps = len(re.findall(r'^\s*[-\*•]\s+', text, re.MULTILINE))
    
    # Pattern 3: Step keywords ("Step 1:", "First,", "Next,", etc.)
    step_keywords = len(re.findall(r'\b(step \d+|first|second|third|next|then|finally|lastly)\b', text, re.IGNORECASE))
    
    return max(numbered_steps, bullet_steps, step_keywords)

def count_citations(sources: List[Dict]) -> int:
    """
    Count valid citations in sources list.
    
    Args:
        sources: List of source dictionaries
        
    Returns:
        Number of valid citations
    """
    if not sources:
        return 0
    
    valid_citations = 0
    for source in sources:
        if isinstance(source, dict) and source.get('name') and source.get('url'):
            valid_citations += 1
    
    return valid_citations

def detect_completeness_issues(text: str) -> List[str]:
    """
    Detect potential completeness issues in answer text.
    
    Args:
        text: Answer text to analyze
        
    Returns:
        List of detected issues
    """
    issues = []
    
    # Truncation indicators
    if text.endswith('...') or text.endswith('..'):
        issues.append("Answer appears truncated")
    
    # Incomplete sentences
    if not text.strip().endswith(('.', '!', '?', ':')):
        issues.append("Answer may be incomplete (no ending punctuation)")
    
    # Vague references
    if re.search(r'\b(as mentioned|as described|see above|follow these|the process)\b', text, re.IGNORECASE):
        if not re.search(r'\d+[\.\)]\s+', text):  # But no actual steps
            issues.append("References steps but doesn't provide them")
    
    # Missing context clues
    if re.search(r'\b(this|that|it|these|those)\b', text, re.IGNORECASE):
        context_ratio = len(re.findall(r'\b(this|that|it|these|those)\b', text, re.IGNORECASE)) / len(text.split())
        if context_ratio > 0.05:  # >5% vague pronouns
            issues.append("Contains many vague references")
    
    return issues

def validate_answer(response_text: str, sources: List[Dict], query: str = "") -> Dict:
    """
    Validate answer quality and suggest improvements.
    
    Args:
        response_text: Generated answer text
        sources: List of source citations
        query: Original query (optional, for context)
        
    Returns:
        Validation result with suggestions
    """
    if not is_enabled():
        return {"valid": True, "suggestions": []}
    
    step_count = count_steps(response_text)
    citation_count = count_citations(sources)
    completeness_issues = detect_completeness_issues(response_text)
    
    suggestions = []
    is_valid = True
    
    # Check step count for procedural queries
    is_procedural = any(keyword in query.lower() for keyword in [
        'how to', 'steps', 'process', 'create', 'convert', 'make'
    ]) if query else False
    
    if is_procedural and step_count < 3:
        suggestions.append("Procedural answer should have at least 3 clear steps")
        is_valid = False
    
    # Check citations
    if citation_count == 0:
        suggestions.append("Answer should include at least one source citation")
        is_valid = False
    
    # Check completeness
    if completeness_issues:
        suggestions.extend(completeness_issues)
        is_valid = False
    
    # Check length for complex queries
    if len(response_text) < 100 and any(word in query.lower() for word in ['explain', 'describe', 'comprehensive']) if query else False:
        suggestions.append("Answer may be too brief for a detailed explanation request")
        is_valid = False
    
    result = {
        "valid": is_valid,
        "step_count": step_count,
        "citation_count": citation_count,
        "suggestions": suggestions,
        "completeness_issues": completeness_issues
    }
    
    if not is_valid:
        logger.warning(f"Answer validation failed: {len(suggestions)} issues found")
    
    return result

def enhance_answer_with_validation(response_text: str, sources: List[Dict], query: str = "") -> str:
    """
    Enhance answer with validation feedback if issues detected.
    
    Args:
        response_text: Original answer
        sources: Source citations  
        query: Original query
        
    Returns:
        Enhanced answer with validation feedback
    """
    if not is_enabled():
        return response_text
    
    validation = validate_answer(response_text, sources, query)
    
    if validation["valid"]:
        return response_text
    
    # Add helpful validation feedback
    enhancement_lines = []
    
    if validation["step_count"] < 3 and any(keyword in query.lower() for keyword in ['how', 'steps', 'process']):
        enhancement_lines.append("*This appears to be a multi-step process. You may need to check the full document for additional steps.*")
    
    if validation["citation_count"] == 0:
        enhancement_lines.append("*Consider checking the source documents directly for complete procedures.*")
    
    if any("truncated" in issue for issue in validation["completeness_issues"]):
        enhancement_lines.append("*This answer may be incomplete. Try asking for specific sections or breaking down your question.*")
    
    if enhancement_lines:
        enhanced_text = response_text + "\n\n" + "\n".join(enhancement_lines)
        logger.info("Enhanced answer with validation feedback")
        return enhanced_text
    
    return response_text