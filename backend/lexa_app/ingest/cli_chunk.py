"""
CLI tool for testing smart chunking on individual PDFs.
"""
import argparse
import json
import sys
from pathlib import Path
from .smart_chunker import smart_chunk

def main():
    parser = argparse.ArgumentParser(description='Test smart chunking on a PDF')
    parser.add_argument('--pdf', required=True, help='Path to PDF file')
    parser.add_argument('--out', required=True, help='Output JSONL file path')
    parser.add_argument('--type', help='Override document type')
    parser.add_argument('--subtype', help='Override document subtype')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    try:
        print(f"Processing: {pdf_path}")
        chunks = smart_chunk(str(pdf_path), args.type, args.subtype)
        
        # Write JSONL output
        with open(args.out, 'w', encoding='utf-8', newline='\n') as f:
            for chunk in chunks:
                f.write(json.dumps(chunk) + '\n')
        
        print(f"Generated {len(chunks)} chunks")
        print(f"Output written to: {args.out}")
        
        if args.verbose:
            total_chars = sum(len(chunk['text']) for chunk in chunks)
            avg_size = total_chars / len(chunks) if chunks else 0
            
            chunk_types = {}
            for chunk in chunks:
                chunk_type = chunk['metadata']['chunk_type']
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
            
            print(f"\nChunk Statistics:")
            print(f"  Total characters: {total_chars}")
            print(f"  Average chunk size: {avg_size:.0f} chars")
            print(f"  Chunk types: {dict(chunk_types)}")
            
            # Show first few chunks
            print(f"\nFirst 3 chunks:")
            for i, chunk in enumerate(chunks[:3]):
                print(f"  {i+1}. Type: {chunk['metadata']['chunk_type']}")
                print(f"     Size: {len(chunk['text'])} chars")
                print(f"     Text: {chunk['text'][:100]}...")
                print()
    
    except Exception as e:
        print(f"Error processing PDF: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()