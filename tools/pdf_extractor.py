"""
PDF text extraction tool
"""

import PyPDF2
from io import BytesIO


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    
    pdf_file = BytesIO(pdf_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    text_parts = []
    for page_num, page in enumerate(pdf_reader.pages):
        text = page.extract_text()
        if text:
            text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
    
    return "\n\n".join(text_parts)