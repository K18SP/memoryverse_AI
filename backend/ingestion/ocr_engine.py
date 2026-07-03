"""
OCR Engine
──────────
Wraps Tesseract via pytesseract.
All parsers that need OCR call ocr_bytes_to_text() — single responsibility.
"""

import io
import asyncio
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

async def ocr_bytes_to_text(img_bytes: bytes) -> str:
    """Run Tesseract OCR on raw PNG/JPEG bytes. Returns cleaned text."""
    loop = asyncio.get_event_loop()
    # Tesseract is CPU-bound; run in thread pool so we don't block the event loop
    text = await loop.run_in_executor(None, _run_tesseract, img_bytes)
    return text


def _run_tesseract(img_bytes: bytes) -> str:
    image = Image.open(io.BytesIO(img_bytes))
    # lang='eng' — add '+hin' etc. for multilingual support later
    raw = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
    # Basic cleanup: collapse multiple blank lines
    lines   = raw.splitlines()
    cleaned = "\n".join(line for line in lines if line.strip())
    return cleaned


async def extract_image(raw_bytes: bytes, filename: str) -> dict:
    """Entry point when the uploaded file IS an image (not a PDF page)."""
    text = await ocr_bytes_to_text(raw_bytes)
    return {
        "text"      : text,
        "extra_meta": {"ocr": True, "source": filename},
    }
