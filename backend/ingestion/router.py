"""
File Type Router
────────────────
Every file uploaded hits detect_and_extract(). It inspects the file's
MIME type / extension, dispatches to the correct parser, and always
returns a normalised dict:

{
    "text"        : str,   # raw extracted text
    "source_type" : str,   # "pdf" | "image" | "docx" | "markdown" | "github"
    "source_file" : str,   # original filename or URL
    "extra_meta"  : dict,  # parser-specific metadata (page count, etc.)
}

Nothing downstream needs to know which parser ran.
"""

import os
import mimetypes
from pathlib import Path
from fastapi import UploadFile, HTTPException

from backend.ingestion.pdf_parser import extract_pdf
from backend.ingestion.ocr_engine import extract_image
from backend.ingestion.docx_parser import extract_docx
from backend.ingestion.markdown_parser import extract_markdown
from backend.ingestion.github_fetcher import extract_github


# Map MIME types → handler tags
MIME_MAP: dict[str, str] = {
    "application/pdf"                                                       : "pdf",
    "image/jpeg"                                                            : "image",
    "image/png"                                                             : "image",
    "image/tiff"                                                            : "image",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/markdown"                                                         : "markdown",
    "text/plain"                                                            : "markdown",   # treat .txt as markdown
}

# Fallback by extension if MIME detection fails
EXT_MAP: dict[str, str] = {
    ".pdf" : "pdf",
    ".jpg" : "image",
    ".jpeg": "image",
    ".png" : "image",
    ".tiff": "image",
    ".tif" : "image",
    ".docx": "docx",
    ".md"  : "markdown",
    ".txt" : "markdown",
}


def _detect_source_type(filename: str, content_type: str | None) -> str:
    """Return a normalised source_type string."""
    # 1. Trust the MIME type if it's in our map
    if content_type and content_type in MIME_MAP:
        return MIME_MAP[content_type]

    # 2. Fall back to file extension
    ext = Path(filename).suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]

    raise HTTPException(
        status_code=415,
        detail=f"Unsupported file type: '{filename}' ({content_type}). "
               f"Supported: PDF, JPG, PNG, DOCX, MD, TXT",
    )


async def detect_and_extract(
    file: UploadFile | None = None,
    github_url: str | None = None,
) -> dict:
    """
    Main dispatcher.

    Pass either:
      - file       : an UploadFile from a multipart form upload
      - github_url : a raw GitHub repo/file URL string
    """

    # ── GitHub URL path ────────────────────────────────────────────────────
    if github_url:
        if not github_url.startswith("https://github.com"):
            raise HTTPException(400, "URL must start with https://github.com")
        result = await extract_github(github_url)
        return {**result, "source_type": "github", "source_file": github_url}

    # ── File upload path ───────────────────────────────────────────────────
    if file is None:
        raise HTTPException(400, "Provide either a file upload or a github_url.")

    source_type = _detect_source_type(file.filename or "", file.content_type)
    raw_bytes   = await file.read()          # read once; pass bytes to parser
    filename    = file.filename or "unknown"

    handlers = {
        "pdf"     : lambda: extract_pdf(raw_bytes, filename),
        "image"   : lambda: extract_image(raw_bytes, filename),
        "docx"    : lambda: extract_docx(raw_bytes, filename),
        "markdown": lambda: extract_markdown(raw_bytes, filename),
    }

    result = await handlers[source_type]()

    return {
        "text"       : result["text"],
        "source_type": source_type,
        "source_file": filename,
        "extra_meta" : result.get("extra_meta", {}),
    }
