"""
OCR utilities for extracting text from PDF pages and images.
"""

import io
import logging

try:
    from pdf2image import convert_from_path

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


def ocr_pdf_page(
    pdf_path: str, page_number: int, dpi: int = 300, lang: str = "eng"
) -> str:
    """
    Extract text from a specific PDF page using OCR.

    Args:
        pdf_path: Path to the PDF file
        page_number: Page number to extract (1-based)
        dpi: DPI for image conversion (default 300)
        lang: OCR language (default "eng")

    Returns:
        Extracted text as string, empty if failed
    """
    if not all([PDF2IMAGE_AVAILABLE, PIL_AVAILABLE, PYTESSERACT_AVAILABLE]):
        logger.warning(
            "OCR dependencies not available (pdf2image, PIL, or pytesseract)"
        )
        return ""

    try:
        # Convert PDF page to image
        images = convert_from_path(
            pdf_path, dpi=dpi, first_page=page_number, last_page=page_number
        )
        if not images:
            logger.warning(f"No images converted from PDF page {page_number}")
            return ""

        img: Image.Image = images[0]

        # Optional pre-processing (convert to grayscale for better OCR)
        if img.mode != "L":  # Not already grayscale
            img = img.convert("L")

        # Run OCR with optimized config
        text = pytesseract.image_to_string(img, lang=lang, config="--oem 3 --psm 6")

        # Clean up the text
        text = text.strip() if text else ""

        logger.debug(
            f"OCR extracted {len(text)} characters from PDF page {page_number}"
        )
        return text

    except Exception as e:
        logger.error(f"OCR failed for PDF page {page_number}: {e}")
        return ""


def ocr_image_bytes(image_bytes: bytes, lang: str = "eng") -> str:
    """
    Extract text from image bytes using OCR.

    Args:
        image_bytes: Image data as bytes
        lang: OCR language (default "eng")

    Returns:
        Extracted text as string, empty if failed
    """
    if not all([PIL_AVAILABLE, PYTESSERACT_AVAILABLE]):
        logger.warning("OCR dependencies not available (PIL or pytesseract)")
        return ""

    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_bytes))

        # Optional pre-processing (convert to grayscale for better OCR)
        if img.mode != "L":  # Not already grayscale
            img = img.convert("L")

        # Run OCR with optimized config
        text = pytesseract.image_to_string(img, lang=lang, config="--oem 3 --psm 6")

        # Clean up the text
        text = text.strip() if text else ""

        logger.debug(f"OCR extracted {len(text)} characters from image")
        return text

    except Exception as e:
        logger.error(f"OCR failed for image: {e}")
        return ""


def count_words(text: str) -> int:
    """Count the number of words in text, handling various word separators."""
    if not text:
        return 0
    return len(text.split())


def ocr_is_available() -> bool:
    """Check if all OCR dependencies are available."""
    return all([PDF2IMAGE_AVAILABLE, PIL_AVAILABLE, PYTESSERACT_AVAILABLE])
