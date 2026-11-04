"""
Simple Image PDF Extractor using pdfplumber (page rendering) + pytesseract OCR.
"""
import os
import pdfplumber
import pytesseract
from processors.text_extractor import (
    extract_account_details,
    extract_transactions_text_fallback,
)

# Auto-locate Tesseract on Windows
for path in [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    r'C:\Users\vinit baria\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
]:
    if os.path.exists(path):
        pytesseract.pytesseract.tesseract_cmd = path
        break


def extract_from_image_pdf(pdf_path: str) -> dict:
    """
    Render PDF pages to images and run Tesseract OCR.
    Extracts account details and transactions from the recognized text.
    """
    try:
        pages_text = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Render page to high-res PIL image and perform OCR
                img = page.to_image(resolution=200).original
                text = pytesseract.image_to_string(img)
                if text:
                    pages_text.append(text)

        full_text = "\n\n".join(pages_text)

        return {
            "account_details": extract_account_details(full_text),
            "transactions": extract_transactions_text_fallback(full_text),
            "extraction_method": "image_ocr",
        }
    except Exception as e:
        return {
            "account_details": {},
            "transactions": [],
            "extraction_method": "image_ocr",
            "error": f"OCR extraction error: {str(e)}",
        }
