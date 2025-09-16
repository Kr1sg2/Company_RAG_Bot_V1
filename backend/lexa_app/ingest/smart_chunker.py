"""
Smart document chunking engine that respects document structure and semantics.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from .section_rules import (
    detect_document_category, extract_step_info, detect_section_headers,
    extract_warnings_and_notes, extract_cross_references, extract_supply_lists,
    detect_form_fields, CHUNK_MIN_CHARS, CHUNK_MAX_CHARS, OVERLAP_TOKENS, MERGE_NEARBY
)

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    from unstructured.partition.pdf import partition_pdf
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    UNSTRUCTURED_AVAILABLE = False

def load_phase2_metadata(doc_filename: str) -> Optional[Dict]:
    """Load Phase 2 enhanced metadata for a document."""
    try:
        metadata_path = Path(__file__).parent.parent.parent / "Database" / "enhanced_metadata.json"
        with open(metadata_path, 'r') as f:
            docs = json.load(f)
        
        for doc in docs:
            if doc['filename'] == doc_filename:
                return doc
    except Exception as e:
        print(f"Could not load Phase 2 metadata: {e}")
    return None

def extract_text_with_pages(pdf_path: str) -> List[Dict]:
    """Extract text with page information."""
    pages = []
    
    if UNSTRUCTURED_AVAILABLE:
        try:
            elements = partition_pdf(pdf_path)
            current_page = 1
            page_text = []
            
            for element in elements:
                if hasattr(element, 'metadata') and element.metadata.page_number:
                    if element.metadata.page_number != current_page:
                        if page_text:
                            pages.append({
                                'page_num': current_page,
                                'text': '\n'.join(page_text)
                            })
                        current_page = element.metadata.page_number
                        page_text = []
                    page_text.append(getattr(element, "text", "") or "")
            
            if page_text:
                pages.append({
                    'page_num': current_page,
                    'text': '\n'.join(page_text)
                })
            
            return pages
        except Exception:
            pass
    
    # Fallback to pdfplumber
    if PDFPLUMBER_AVAILABLE:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages.append({
                            'page_num': i + 1,
                            'text': text
                        })
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
    
    return pages

def chunk_procedure_steps(text: str, parent_section: str = "") -> List[Dict]:
    """Chunk text by procedure steps."""
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_step = None
    step_count = 0
    
    for line in lines:
        step_info = extract_step_info(line)
        
        if step_info:
            # Save previous chunk
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if len(chunk_text) >= CHUNK_MIN_CHARS:
                    chunks.append({
                        'text': chunk_text,
                        'chunk_type': 'procedure_steps',
                        'parent_section': parent_section,
                        'step_number': current_step,
                        'step_count': step_count
                    })
                current_chunk = []
            
            # Start new chunk
            current_step = step_info['step_number']
            step_count += 1
            current_chunk.append(line)
        else:
            current_chunk.append(line)
            
            # Check if chunk is getting too large
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text) > CHUNK_MAX_CHARS:
                # Find a good break point
                break_point = find_sentence_boundary(chunk_text, CHUNK_MAX_CHARS - 200)
                if break_point:
                    chunks.append({
                        'text': chunk_text[:break_point] + " (cont.)",
                        'chunk_type': 'procedure_steps',
                        'parent_section': parent_section,
                        'step_number': current_step,
                        'step_count': step_count
                    })
                    current_chunk = [chunk_text[break_point:]]
    
    # Save final chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk).strip()
        if len(chunk_text) >= CHUNK_MIN_CHARS:
            chunks.append({
                'text': chunk_text,
                'chunk_type': 'procedure_steps',
                'parent_section': parent_section,
                'step_number': current_step,
                'step_count': step_count
            })
    
    return chunks

def chunk_policy_sections(text: str) -> List[Dict]:
    """Chunk text by policy sections."""
    chunks = []
    headers = detect_section_headers(text)
    
    if not headers:
        # No clear structure, fall back to size-based chunking
        return chunk_by_size(text, 'policy_section')
    
    sections = []
    lines = text.split('\n')
    
    for i in range(len(headers)):
        start_line = headers[i][1]
        end_line = headers[i + 1][1] if i + 1 < len(headers) else len(lines)
        
        section_text = '\n'.join(lines[start_line:end_line]).strip()
        if section_text:
            sections.append({
                'header': headers[i][0],
                'text': section_text,
                'header_type': headers[i][2]
            })
    
    for section in sections:
        if len(section['text']) <= CHUNK_MAX_CHARS:
            chunks.append({
                'text': section['text'],
                'chunk_type': 'policy_section',
                'section_header': section['header'],
                'header_type': section['header_type']
            })
        else:
            # Split large sections
            sub_chunks = chunk_by_size(section['text'], 'policy_section')
            for i, chunk in enumerate(sub_chunks):
                chunk['section_header'] = section['header']
                chunk['header_type'] = section['header_type']
                chunk['section_part'] = i + 1
                chunks.append(chunk)
    
    return chunks

def chunk_form_content(text: str) -> List[Dict]:
    """Chunk form content by field groups."""
    form_info = detect_form_fields(text)
    
    if not form_info['has_form_fields']:
        return chunk_by_size(text, 'form_general')
    
    # Simple approach: split by major sections or size
    chunks = chunk_by_size(text, 'form_table_desc')
    
    for chunk in chunks:
        chunk.update({
            'has_table': form_info['field_count'] > 5,
            'field_count': form_info['field_count'] // len(chunks)
        })
    
    return chunks

def chunk_by_size(text: str, chunk_type: str = 'general') -> List[Dict]:
    """Fallback chunking by size with sentence boundaries."""
    chunks = []
    
    if len(text) <= CHUNK_MAX_CHARS:
        return [{
            'text': text,
            'chunk_type': chunk_type
        }]
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        
        if current_length + sentence_length > CHUNK_MAX_CHARS and current_chunk:
            # Save current chunk
            chunk_text = ' '.join(current_chunk)
            if len(chunk_text) >= CHUNK_MIN_CHARS:
                chunks.append({
                    'text': chunk_text,
                    'chunk_type': chunk_type
                })
            
            # Start new chunk with overlap
            if OVERLAP_TOKENS > 0 and len(current_chunk) > 1:
                overlap_sentences = current_chunk[-1:]  # Take last sentence as overlap
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk = [sentence]
                current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length
    
    # Save final chunk
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        if len(chunk_text) >= CHUNK_MIN_CHARS:
            chunks.append({
                'text': chunk_text,
                'chunk_type': chunk_type
            })
    
    return chunks

def find_sentence_boundary(text: str, target_pos: int) -> Optional[int]:
    """Find the nearest sentence boundary before target position."""
    if target_pos >= len(text):
        return None
    
    # Look backwards for sentence endings
    for i in range(target_pos, max(0, target_pos - 200), -1):
        if text[i] in '.!?' and i + 1 < len(text) and text[i + 1].isspace():
            return i + 1
    
    return None

def find_page_range(chunk_text: str, pages: List[Dict]) -> tuple:
    """Find the page range for a chunk of text using Jaccard similarity."""
    stop = {
        "the","and","of","to","in","a","for","is","on","with","by","as","at","from",
        "or","an","be","are","this","that","it","if","then","you","your","we","our"
    }
    def tokens(s: str):
        return {w for w in re.findall(r"[A-Za-z0-9\-]{3,}", s.lower()) if w not in stop}

    c = tokens(chunk_text)
    if not c:
        return 1, 1

    scores = []
    for p in pages:
        pw = tokens(p.get("text",""))
        inter = len(c & pw)
        union = len(c | pw) or 1
        j = inter / union
        scores.append((j, p["page_num"]))

    scores.sort(reverse=True)  # highest Jaccard first
    top = [pg for _, pg in scores[:2] if _ > 0]
    if not top:
        return 1, 1
    return (min(top), max(top))

def smart_chunk(pdf_path: str, doc_type: str = None, subtype: str = None) -> List[Dict]:
    """Main smart chunking function."""
    pdf_path = Path(pdf_path)
    
    # Load Phase 2 metadata
    metadata = load_phase2_metadata(pdf_path.name)
    if metadata:
        doc_type = metadata.get('type', doc_type)
        subtype = metadata.get('subtype', subtype)
        title = metadata.get('title', pdf_path.stem)
        keywords = metadata.get('keywords', [])
    else:
        title = pdf_path.stem
        keywords = []
    
    # Extract text with page information
    pages = extract_text_with_pages(str(pdf_path))
    if not pages:
        return []
    
    full_text = '\n'.join(page['text'] for page in pages)
    
    # Detect document category
    category = detect_document_category(full_text, doc_type)
    
    # Hybrid detection: if a "form" doc clearly contains steps, run both strategies
    contains_steps = bool(re.search(r'^\s*(?:step\s*)?\d+[\.\):]\s+', full_text, re.IGNORECASE | re.MULTILINE))
    if (category == 'form' or (doc_type == 'form')) and contains_steps:
        chunks_form = chunk_form_content(full_text)
        chunks_proc = chunk_procedure_steps(full_text, "Embedded Procedure")
        chunks = chunks_proc + chunks_form
    else:
        # Choose chunking strategy based on category
        if category == 'product_care' or (doc_type == 'user_manual'):
            chunks = chunk_procedure_steps(full_text, "Product Care")
        elif category == 'netsuite_guide' or (doc_type == 'netsuite_guide'):
            chunks = chunk_procedure_steps(full_text, "NetSuite Guide")
        elif category == 'policy' or (doc_type == 'business_process'):
            chunks = chunk_policy_sections(full_text)
        elif category == 'form' or (doc_type == 'form'):
            chunks = chunk_form_content(full_text)
        else:
            chunks = chunk_by_size(full_text, 'general')
    
    # Enhance chunks with metadata
    enhanced_chunks = []
    for i, chunk in enumerate(chunks):
        # Find page range for this chunk
        page_start, page_end = find_page_range(chunk['text'], pages)
        
        # Extract additional metadata
        warnings = extract_warnings_and_notes(chunk['text'])
        cross_refs = extract_cross_references(chunk['text'])
        supplies = extract_supply_lists(chunk['text'])
        
        enhanced_chunk = {
            'text': chunk['text'],
            'metadata': {
                'doc_filename': pdf_path.name,
                'doc_type': doc_type or 'unknown',
                'doc_subtype': subtype or 'general',
                'doc_title': title,
                'chunk_index': i,
                'chunk_type': chunk.get('chunk_type', 'general'),
                'page_start': page_start,
                'page_end': page_end,
                'keywords': keywords,
                'warnings': warnings,
                'cross_refs': cross_refs,
                'supplies': supplies,
                'char_count': len(chunk['text']),
                **{k: v for k, v in chunk.items() if k != 'text'}
            }
        }
        
        enhanced_chunks.append(enhanced_chunk)
    
    # Merge nearby small chunks if enabled
    if MERGE_NEARBY:
        enhanced_chunks = merge_small_chunks(enhanced_chunks)
    
    return enhanced_chunks

def merge_small_chunks(chunks: List[Dict]) -> List[Dict]:
    """Merge adjacent small chunks of the same type."""
    if len(chunks) <= 1:
        return chunks
    
    merged = []
    current_chunk = chunks[0]
    
    for next_chunk in chunks[1:]:
        current_size = len(current_chunk['text'])
        next_size = len(next_chunk['text'])
        same_type = (current_chunk['metadata']['chunk_type'] == 
                    next_chunk['metadata']['chunk_type'])
        
        # Merge if both chunks are small and of the same type
        if (current_size < CHUNK_MIN_CHARS * 2 and 
            next_size < CHUNK_MIN_CHARS * 2 and
            same_type and
            current_size + next_size <= CHUNK_MAX_CHARS):
            
            # Merge the chunks
            current_chunk['text'] += '\n\n' + next_chunk['text']
            current_chunk['metadata']['char_count'] = len(current_chunk['text'])
            current_chunk['metadata']['page_end'] = next_chunk['metadata']['page_end']
            
            # Merge lists in metadata
            for key in ['warnings', 'cross_refs', 'supplies']:
                current_chunk['metadata'].setdefault(key, [])
                next_vals = (next_chunk['metadata'].get(key) or [])
                current_chunk['metadata'][key].extend(next_vals)
        else:
            merged.append(current_chunk)
            current_chunk = next_chunk
    
    merged.append(current_chunk)
    
    # Update chunk indices
    for i, chunk in enumerate(merged):
        chunk['metadata']['chunk_index'] = i
    
    return merged