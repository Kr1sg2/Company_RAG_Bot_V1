"""
Table extraction from PDFs using camelot with fallbacks.
"""

import logging
from typing import List, Dict

try:
    import camelot
    CAMELOT_AVAILABLE = True
except ImportError:
    CAMELOT_AVAILABLE = False

logger = logging.getLogger(__name__)

class TableExtractor:
    def __init__(self):
        self.available = CAMELOT_AVAILABLE
        if not self.available:
            logger.warning("Table extraction not available - missing camelot-py")
            
    def extract_tables_from_page(self, pdf_path: str, page_num: int) -> List[Dict]:
        """
        Extract tables from a specific page.
        Returns list of table dictionaries with metadata.
        """
        if not self.available:
            return []
            
        tables = []
        
        try:
            # Try lattice method first (better for bordered tables)
            lattice_tables = camelot.read_pdf(
                pdf_path,
                pages=str(page_num),
                flavor='lattice',
                line_scale=40
            )
            
            for i, table in enumerate(lattice_tables):
                if table.accuracy > 50:  # Only keep reasonably accurate tables
                    tables.append({
                        'page': page_num,
                        'table_index': i,
                        'method': 'lattice',
                        'accuracy': table.accuracy,
                        'data': table.df.to_dict('records'),
                        'csv': table.df.to_csv(index=False),
                        'shape': table.shape
                    })
                    
        except Exception as e:
            logger.debug(f"Lattice table extraction failed on page {page_num}: {e}")
            
        # If no good lattice tables, try stream method
        if not tables:
            try:
                stream_tables = camelot.read_pdf(
                    pdf_path,
                    pages=str(page_num),
                    flavor='stream',
                    edge_tol=500
                )
                
                for i, table in enumerate(stream_tables):
                    if table.accuracy > 30:  # Lower threshold for stream
                        tables.append({
                            'page': page_num,
                            'table_index': i,
                            'method': 'stream',
                            'accuracy': table.accuracy,
                            'data': table.df.to_dict('records'),
                            'csv': table.df.to_csv(index=False),
                            'shape': table.shape
                        })
                        
            except Exception as e:
                logger.debug(f"Stream table extraction failed on page {page_num}: {e}")
                
        if tables:
            logger.info(f"Extracted {len(tables)} tables from page {page_num}")
            
        return tables
        
    def tables_to_text(self, tables: List[Dict]) -> str:
        """Convert extracted tables to searchable text format."""
        if not tables:
            return ""
            
        text_parts = []
        
        for table in tables:
            try:
                # Add table metadata
                text_parts.append(f"TABLE {table['table_index']} (accuracy: {table['accuracy']:.1f}%):")
                
                # Add CSV representation for better searchability
                csv_text = table['csv']
                text_parts.append(csv_text)
                text_parts.append("")  # Empty line between tables
                
            except Exception as e:
                logger.warning(f"Failed to convert table to text: {e}")
                continue
                
        return "\n".join(text_parts)

# Global table extractor instance
table_extractor = TableExtractor()