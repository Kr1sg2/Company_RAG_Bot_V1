"""
OCR utilities using pdf2image and pytesseract.
"""

import os
import logging
from typing import Optional, Tuple
from io import BytesIO

try:
    from pdf2image import convert_from_path, convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self):
        self.available = all([PDF2IMAGE_AVAILABLE, PIL_AVAILABLE, PYTESSERACT_AVAILABLE])
        if not self.available:
            logger.warning("OCR not available - missing dependencies (pdf2image, PIL, or pytesseract)")
            
    def extract_page_text(self, pdf_path: str, page_num: int, dpi: int = 300) -> Tuple[str, int]:
        """
        Extract text from a PDF page using OCR.
        Returns: (text, word_count)
        """
        if not self.available:
            return "", 0
            
        try:
            # Convert PDF page to image
            images = convert_from_path(pdf_path, dpi=dpi, first_page=page_num, last_page=page_num)
            
            if not images:
                logger.warning(f"No images converted from PDF page {page_num}")
                return "", 0
                
            img = images[0]
            
            # Convert to grayscale for better OCR
            if img.mode != 'L':
                img = img.convert('L')
                
            # Run OCR with optimized config
            text = pytesseract.image_to_string(img, lang='eng', config='--oem 3 --psm 6')
            text = text.strip() if text else ""
            
            word_count = len(text.split()) if text else 0
            
            logger.debug(f"OCR extracted {word_count} words from page {page_num}")
            return text, word_count
            
        except Exception as e:
            logger.error(f"OCR failed for page {page_num}: {e}")
            return "", 0
            
    def extract_from_bytes(self, pdf_bytes: bytes, page_num: int, dpi: int = 300) -> Tuple[str, int]:
        """Extract text from PDF bytes."""
        if not self.available:
            return "", 0
            
        try:
            images = convert_from_bytes(pdf_bytes, dpi=dpi, first_page=page_num, last_page=page_num)
            
            if not images:
                return "", 0
                
            img = images[0]
            
            if img.mode != 'L':
                img = img.convert('L')
                
            text = pytesseract.image_to_string(img, lang='eng', config='--oem 3 --psm 6')
            text = text.strip() if text else ""
            
            word_count = len(text.split()) if text else 0
            return text, word_count
            
        except Exception as e:
            logger.error(f"OCR failed for PDF bytes page {page_num}: {e}")
            return "", 0

# Global OCR processor instance
ocr_processor = OCRProcessor()