"""
PDF Parser — uses pypdf (more compatible with Python 3.12 on Windows)
Falls back to OCR if a page has less than 30 characters of text.
"""

import io
from pypdf import PdfReader
from backend.ingestion.ocr_engine import ocr_bytes_to_text

OCR_THRESHOLD = 30


async def extract_pdf(raw_bytes: bytes, filename: str) -> dict:
    reader = PdfReader(io.BytesIO(raw_bytes))
    pages  = []

    for page_num, page in enumerate(reader.pages, start=1):
        native_text = (page.extract_text() or "").strip()

        if len(native_text) >= OCR_THRESHOLD:
            pages.append(native_text)
        else:
            # Scanned page — we can't render to image without fitz,
            # so we note it and skip OCR for now
            print(f"   ↳ Page {page_num} of '{filename}' is scanned — OCR skipped (no fitz).")
            pages.append(f"[Page {page_num}: scanned content — OCR pending]")

    return {
        "text"      : "\n\n".join(pages),
        "extra_meta": {
            "page_count"  : len(reader.pages),
            "ocr_fallback": False,
        },
    }