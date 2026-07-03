"""
Markdown / Plain-text Parser
─────────────────────────────
Strips Markdown syntax and returns clean plain text.
Also handles .txt files (treated identically).
"""

import re
import markdown as md_lib


async def extract_markdown(raw_bytes: bytes, filename: str) -> dict:
    raw_text = raw_bytes.decode("utf-8", errors="replace")

    if filename.endswith(".md"):
        # Convert MD → HTML → strip tags for clean plain text
        html  = md_lib.markdown(raw_text)
        clean = _strip_html_tags(html)
    else:
        clean = raw_text                 # .txt — use as-is

    return {
        "text"      : clean.strip(),
        "extra_meta": {"format": "markdown" if filename.endswith(".md") else "plaintext"},
    }


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags, collapse whitespace."""
    no_tags = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s{2,}", "\n", no_tags)
