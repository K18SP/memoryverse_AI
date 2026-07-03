"""
Embedding Generator — FREE local sentence-transformers
No API key needed. Runs on your machine.
Model: all-MiniLM-L6-v2 (384 dimensions)
"""

from sentence_transformers import SentenceTransformer
from functools import lru_cache

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM   = 384


@lru_cache()
def get_model() -> SentenceTransformer:
    """Load model once, reuse across all requests."""
    print("   Loading embedding model (first time only)...")
    return SentenceTransformer(EMBEDDING_MODEL)


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate 384-dim embeddings for a list of texts."""
    if not texts:
        return []

    import asyncio
    model  = get_model()
    loop   = asyncio.get_event_loop()

    vectors = await loop.run_in_executor(
        None,
        lambda: model.encode(texts, convert_to_numpy=True).tolist()
    )
    return vectors


async def generate_single_embedding(text: str) -> list[float]:
    """Single text embedding — used in search."""
    results = await generate_embeddings([text])
    return results[0] if results else []