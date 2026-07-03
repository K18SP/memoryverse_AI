"""
Chunker
───────
Splits a long text into overlapping chunks so that:
  - No chunk exceeds max_tokens (default 512)
  - Consecutive chunks share overlap_tokens (default 50)
    so context at boundaries is never lost.

Why tiktoken?
  tiktoken counts tokens the same way OpenAI's embedding
  model does — so we never accidentally send an oversized
  chunk to the API.

Returns a list of dicts:
  {
    "text"      : str,   # chunk text
    "chunk_index": int,  # position in document (0-based)
    "token_count": int,  # exact token count
  }
"""

import tiktoken
from backend.config import get_settings

# Encoding used by text-embedding-3-small and text-embedding-3-large
ENCODING_NAME = "cl100k_base"


def chunk_text(
    text      : str,
    max_tokens: int | None = None,
    overlap   : int | None = None,
) -> list[dict]:
    """
    Split text into overlapping token-bounded chunks.

    Args:
        text       : raw extracted text from any parser
        max_tokens : max tokens per chunk (default from settings)
        overlap    : overlap tokens between chunks (default from settings)

    Returns:
        List of chunk dicts with text, chunk_index, token_count
    """
    settings   = get_settings()
    max_tokens = max_tokens or settings.chunk_size      # 512
    overlap    = overlap    or settings.chunk_overlap   # 50

    if not text or not text.strip():
        return []

    enc    = tiktoken.get_encoding(ENCODING_NAME)
    tokens = enc.encode(text)

    # Nothing to chunk — fits in a single chunk
    if len(tokens) <= max_tokens:
        return [{
            "text"        : text.strip(),
            "chunk_index" : 0,
            "token_count" : len(tokens),
        }]

    chunks  = []
    start   = 0
    idx     = 0

    while start < len(tokens):
        end        = min(start + max_tokens, len(tokens))
        chunk_toks = tokens[start:end]
        chunk_text = enc.decode(chunk_toks).strip()

        if chunk_text:                          # skip empty chunks
            chunks.append({
                "text"        : chunk_text,
                "chunk_index" : idx,
                "token_count" : len(chunk_toks),
            })
            idx += 1

        # Slide forward by (max_tokens - overlap)
        # so the next chunk starts overlap tokens before this one ended
        start += max_tokens - overlap

    return chunks