"""
PDF Type Detector - Determines if a PDF is text-based or image-based (scanned)
"""
import pdfplumber


def detect_pdf_type(pdf_path: str) -> str:
    """
    Detect whether a PDF is text-based or image-based.
    Returns 'text' or 'image'.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_chars = 0
            total_pages = len(pdf.pages)

            for page in pdf.pages[:min(3, total_pages)]:  # Check first 3 pages
                text = page.extract_text() or ""
                total_chars += len(text.strip())

            # If average chars per page is too low, it's likely image-based
            avg_chars = total_chars / max(1, min(3, total_pages))
            if avg_chars < 50:
                return "image"
            return "text"
    except Exception:
        return "text"

