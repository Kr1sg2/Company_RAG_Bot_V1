"""
Document structure extraction for TOC/heading-aware RAG.
Extracts PDF bookmarks and detects headings via text heuristics.
"""
import os
import re
import logging
from typing import List, Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)

# Feature flags
def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name, str(default))
    return v.strip().lower() in ("1", "true", "yes", "on")

USE_TOC = lambda: env_bool("LEXA_USE_TOC", True)
TOC_WEIGHT = lambda: float(os.getenv("LEXA_TOC_WEIGHT", "1.10"))
HEADING_WEIGHT = lambda: float(os.getenv("LEXA_HEADING_WEIGHT", "1.05"))

# Boilerplate patterns to ignore when detecting headings
IGNORE_PATTERNS = [
    r"^page\s+\d+\s+of\s+\d+$",
    r"^table of contents$", 
    r"^\d{1,2}/\d{1,2}/\d{2,4}$",
    r"^copyright\s+\d{4}",
    r"^all rights reserved",
    r"^\d+$",  # Just numbers
]

def extract_pdf_outline(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract PDF bookmarks/outline using PyMuPDF if available."""
    if not USE_TOC():
        return []
    
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        toc = doc.get_toc(simple=False)  # Get detailed TOC with page info
        doc.close()
        
        if not toc:
            return []
            
        # Convert to our format: [{'level': int, 'title': str, 'page': int}]
        outline = []
        for level, title, page in toc:
            if title and title.strip() and page > 0:
                outline.append({
                    'level': max(0, level - 1),  # Normalize to 0-based
                    'title': title.strip(),
                    'page': page,  # PyMuPDF pages are 1-based
                    'source': 'bookmark'
                })
        
        logger.info(f"Extracted {len(outline)} PDF bookmarks from {os.path.basename(pdf_path)}")
        return outline
        
    except ImportError:
        logger.debug("PyMuPDF not available, skipping PDF outline extraction")
        return []
    except Exception as e:
        logger.warning(f"Failed to extract PDF outline from {pdf_path}: {e}")
        return []

def detect_headings_by_text(text: str, page_num: int) -> List[Dict[str, Any]]:
    """Detect headings in text using heuristics."""
    if not USE_TOC():
        return []
        
    headings = []
    lines = text.split('\n')
    
    for line_idx, line in enumerate(lines[:20]):  # Only check first 20 lines per page
        line = line.strip()
        if len(line) < 3 or len(line) > 100:  # Skip too short/long
            continue
            
        # Skip boilerplate patterns
        if any(re.match(pattern, line.lower()) for pattern in IGNORE_PATTERNS):
            continue
            
        # Heuristic heading detection
        is_heading = False
        heading_level = 0
        
        # Pattern 1: Numbered sections "1. Something" or "1 Something"
        numbered_match = re.match(r'^(\d+)\.?\s+([A-Z][^.!?]*)', line)
        if numbered_match:
            level_num = int(numbered_match.group(1))
            is_heading = True
            heading_level = min(level_num - 1, 3) if level_num <= 4 else 2
        
        # Pattern 2: ALL CAPS (but not too long)
        elif line.isupper() and len(line) <= 60:
            is_heading = True
            heading_level = 1
            
        # Pattern 3: Title Case and short
        elif line.istitle() and len(line) <= 60 and not line.endswith('.'):
            # Additional check: must have few function words
            words = line.split()
            if len(words) >= 2 and len([w for w in words if w.lower() in ['the', 'of', 'and', 'to', 'in', 'for', 'on', 'with']]) <= len(words) // 3:
                is_heading = True
                heading_level = 2
                
        # Pattern 4: Ends with colon (section introducers)
        elif line.endswith(':') and len(line.split()) <= 8:
            is_heading = True
            heading_level = 2
            
        if is_heading:
            headings.append({
                'level': heading_level,
                'title': line,
                'page': page_num,
                'line': line_idx,
                'source': 'heuristic'
            })
    
    return headings

def build_heading_index(pdf_path: str, pages_text: Dict[int, str]) -> List[Dict[str, Any]]:
    """Build complete heading index from PDF bookmarks + text heuristics."""
    if not USE_TOC():
        return []
        
    # Get PDF outline first
    outline_headings = extract_pdf_outline(pdf_path)
    
    # Get text-based headings
    text_headings = []
    for page_num, text in pages_text.items():
        page_headings = detect_headings_by_text(text, page_num)
        text_headings.extend(page_headings)
    
    # Combine and deduplicate
    all_headings = outline_headings + text_headings
    
    # Sort by page, then by line if available
    all_headings.sort(key=lambda h: (h['page'], h.get('line', 0)))
    
    # Simple deduplication: remove headings with very similar titles on same page
    deduplicated = []
    for heading in all_headings:
        title_lower = heading['title'].lower()
        
        # Check if we already have a very similar heading on the same page
        similar_found = False
        for existing in deduplicated:
            if (existing['page'] == heading['page'] and 
                _text_similarity(existing['title'].lower(), title_lower) > 0.8):
                # Keep the bookmark version if we have both
                if heading['source'] == 'bookmark' and existing['source'] == 'heuristic':
                    deduplicated.remove(existing)
                    break
                else:
                    similar_found = True
                    break
        
        if not similar_found:
            deduplicated.append(heading)
    
    logger.info(f"Built heading index for {os.path.basename(pdf_path)}: "
                f"{len(outline_headings)} bookmarks + {len(text_headings)} text = {len(deduplicated)} final")
    
    return deduplicated

def _text_similarity(text1: str, text2: str) -> float:
    """Simple text similarity using word overlap."""
    words1 = set(re.findall(r'\b\w+\b', text1.lower()))
    words2 = set(re.findall(r'\b\w+\b', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
        
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    
    return intersection / union if union > 0 else 0.0

def build_heading_paths(headings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build hierarchical paths for headings (breadcrumbs)."""
    if not headings:
        return []
    
    # Add h_path to each heading
    path_stack = []  # Stack of (level, title) tuples
    
    for heading in headings:
        level = heading['level']
        title = heading['title']
        
        # Pop stack until we find the right parent level
        while path_stack and path_stack[-1][0] >= level:
            path_stack.pop()
        
        # Add current heading to stack
        path_stack.append((level, title))
        
        # Build path string
        path_parts = [part[1] for part in path_stack]
        heading['h_path'] = ' > '.join(path_parts) if len(path_parts) > 1 else title
    
    return headings

def tag_chunk(chunk_text: str, page: int, chunk_index: int, heading_index: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tag a chunk with structural metadata based on nearest heading."""
    if not USE_TOC() or not heading_index:
        return {}
    
    # Find the most recent heading at or before this page
    relevant_heading = None
    
    for heading in reversed(heading_index):  # Start from end (most recent)
        if heading['page'] <= page:
            relevant_heading = heading
            break
    
    if not relevant_heading:
        return {}
    
    # Build metadata
    metadata = {
        'section': relevant_heading['title'],
        'h_path': relevant_heading.get('h_path', relevant_heading['title']),
        'heading_rank': relevant_heading['level'],
        'page_start': page,
        'page_end': page,  # Single page for now; could be enhanced
    }
    
    return metadata

def extract_structure_for_document(pdf_path: str, pages_text: Dict[int, str]) -> List[Dict[str, Any]]:
    """Main entry point: extract complete document structure."""
    if not USE_TOC():
        logger.debug(f"TOC extraction disabled for {os.path.basename(pdf_path)}")
        return []
        
    try:
        # Build heading index
        headings = build_heading_index(pdf_path, pages_text)
        
        # Add hierarchical paths
        headings_with_paths = build_heading_paths(headings)
        
        logger.info(f"Structure extraction complete for {os.path.basename(pdf_path)}: "
                   f"{len(headings_with_paths)} headings across {len(pages_text)} pages")
        
        return headings_with_paths
        
    except Exception as e:
        logger.error(f"Structure extraction failed for {pdf_path}: {e}")
        return []