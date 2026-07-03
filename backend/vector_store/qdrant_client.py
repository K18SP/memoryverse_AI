"""
Qdrant vector store — collection initialisation and shared async client.

Collection schema
─────────────────
Each point represents ONE text chunk from an uploaded document.

Vector : 1536-dim float (text-embedding-3-small)
         swap to 3072-dim if using text-embedding-3-large

Payload fields (stored alongside every vector):
  chunk_id     : str   — UUID for this chunk
  user_id      : str   — owner of the document
  text         : str   — raw chunk text (used for BM25 + citation display)
  source_type  : str   — "pdf" | "image" | "docx" | "markdown" | "github"
  source_file  : str   — original filename or URL
  date         : str   — ISO date string (YYYY-MM or YYYY-MM-DD)
  category     : str   — assigned by LLM categoriser (Block 2)
  entities     : list  — extracted named entities (Block 3)
  skills       : list  — extracted skills (Block 3)
  trust_score  : int   — credential trust score 0-100 (Block 5)
"""

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    PayloadSchemaType,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)
from qdrant_client.models import PointStruct
from functools import lru_cache
from backend.config import get_settings

# ── Embedding dimensions ───────────────────────────────────────────────────
DENSE_DIM = 384          # text-embedding-3-small  (change to 3072 for large)


@lru_cache()
def get_qdrant_client() -> AsyncQdrantClient:
    """Return a singleton async Qdrant client."""
    settings = get_settings()
    return AsyncQdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


async def init_qdrant_collection() -> None:
    """
    Create the collection the first time the app starts.
    Safe to call on every restart — skips creation if already exists.
    """
    settings = get_settings()
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection

    existing = await client.get_collections()
    names = [c.name for c in existing.collections]

    if collection_name in names:
        print(f"   Collection '{collection_name}' already exists — skipping.")
        return

    # Create with BOTH dense (semantic) and sparse (BM25) vector support
    await client.create_collection(
        collection_name=collection_name,
        vectors_config={
            "dense": VectorParams(
                size=DENSE_DIM,
                distance=Distance.COSINE,
            )
        },
        sparse_vectors_config={
            "sparse": SparseVectorParams(
                index=SparseIndexParams(on_disk=False)
            )
        },
    )

    # Create payload indexes for fast filtering
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="user_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="source_type",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=collection_name,
        field_name="category",
        field_schema=PayloadSchemaType.KEYWORD,
    )

    print(f"   Collection '{collection_name}' created with dense + sparse vectors.")

async def upsert_chunks(chunks_with_vectors: list[dict]) -> int:
    """
    Upsert a batch of chunks into Qdrant.

    Args:
        chunks_with_vectors: list of dicts, each containing:
            - "payload" : DocChunk.to_payload() dict
            - "vector"  : list[float] — the dense embedding

    Returns:
        Number of points upserted
    """
    settings   = get_settings()
    client     = get_qdrant_client()

    points = [
        PointStruct(
            id      = item["payload"]["chunk_id"],
            vector  = {"dense": item["vector"]},
            payload = item["payload"],
        )
        for item in chunks_with_vectors
    ]

    await client.upsert(
        collection_name = settings.qdrant_collection,
        points          = points,
        wait            = True,       # wait for indexing before returning
    )

    return len(points)


async def delete_user_documents(user_id: str) -> None:
    """Delete all indexed chunks for a user from Qdrant."""
    settings = get_settings()
    client = get_qdrant_client()

    await client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=user_id),
                    )
                ]
            )
        ),
        wait=True,
    )
