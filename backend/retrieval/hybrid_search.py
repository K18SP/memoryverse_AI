"""
Hybrid Search
─────────────
Combines two retrieval strategies and fuses their scores:

1. DENSE search  — cosine similarity over 384-dim embeddings
                   finds semantically similar chunks even if
                   exact words don't match.

2. BM25 search   — keyword frequency scoring (lexical)
                   nails exact names, acronyms, company names.

Fusion: Reciprocal Rank Fusion (RRF)
  score = 1 / (rank + 60)
  Final ranking = sum of RRF scores from both lists.
  The constant 60 dampens the impact of high ranks.
"""

from qdrant_client.models import Filter, FieldCondition, MatchValue
from rank_bm25 import BM25Okapi
from backend.vector_store.qdrant_client import get_qdrant_client
from backend.embeddings.generator import generate_single_embedding
from backend.config import get_settings


# ── RRF constant — standard value from the original paper ─────────────────
RRF_K = 60


async def hybrid_search(
    query      : str,
    user_id    : str,
    top_k      : int = 5,
    score_threshold: float = 0.0,
) -> list[dict]:
    """
    Run hybrid search for a user's query against their documents.

    Args:
        query   : natural language query string
        user_id : only search this user's documents
        top_k   : number of final results to return

    Returns:
        List of chunk dicts sorted by fused relevance score, each containing:
          text, source_file, source_type, date, score, chunk_id
    """
    settings = get_settings()
    client   = get_qdrant_client()

    # ── Step 1: Dense vector search ────────────────────────────────────────
    # Filter to only this user's documents
    user_filter  = Filter(
        must=[FieldCondition(
            key="user_id",
            match=MatchValue(value=user_id)
        )]
    )

    try:
        query_vector = await generate_single_embedding(query)
        dense_results = await client.search(
            collection_name = settings.qdrant_collection,
            query_vector    = ("dense", query_vector),
            query_filter    = user_filter,
            limit           = top_k * 3,
            with_payload    = True,
        )
    except Exception:
        dense_results = []

    full_lexical_results = await _lexical_fallback_search(
        client=client,
        collection_name=settings.qdrant_collection,
        user_filter=user_filter,
        query=query,
        top_k=top_k * 3,
    )

    if not dense_results:
        return full_lexical_results[:top_k]

    # ── Step 2: BM25 lexical search over retrieved chunks ──────────────────
    # We run BM25 on the candidate pool from dense search
    # (not the entire collection — that would be too slow)
    candidates = [
        {
            "chunk_id"   : hit.payload["chunk_id"],
            "text"       : hit.payload["text"],
            "source_file": hit.payload["source_file"],
            "source_type": hit.payload["source_type"],
            "date"       : hit.payload.get("date", ""),
            "category"   : hit.payload.get("category", ""),
            "original_file_url": hit.payload.get("original_file_url", ""),
            "dense_score": hit.score,
        }
        for hit in dense_results
    ]

    seen_ids = {c["chunk_id"] for c in candidates}
    for item in full_lexical_results:
        if item["chunk_id"] in seen_ids:
            continue
        candidates.append({
            "chunk_id": item["chunk_id"],
            "text": item["text"],
            "source_file": item["source_file"],
            "source_type": item["source_type"],
            "date": item["date"],
            "category": item["category"],
            "original_file_url": item.get("original_file_url", ""),
            "dense_score": item.get("dense_score", 0.0),
        })
        seen_ids.add(item["chunk_id"])

    # Tokenise for BM25
    tokenised_corpus = [c["text"].lower().split() for c in candidates]
    bm25             = BM25Okapi(tokenised_corpus)
    query_tokens     = query.lower().split()
    bm25_scores      = bm25.get_scores(query_tokens)

    # ── Step 3: Reciprocal Rank Fusion ─────────────────────────────────────
    # Build rank lists for both methods
    dense_ranked = sorted(
        range(len(candidates)),
        key=lambda i: candidates[i]["dense_score"],
        reverse=True
    )
    bm25_ranked  = sorted(
        range(len(candidates)),
        key=lambda i: bm25_scores[i],
        reverse=True
    )

    # RRF score for each candidate
    rrf_scores = [0.0] * len(candidates)

    for rank, idx in enumerate(dense_ranked):
        rrf_scores[idx] += 1.0 / (rank + RRF_K)

    for rank, idx in enumerate(bm25_ranked):
        rrf_scores[idx] += 1.0 / (rank + RRF_K)

    # ── Step 4: Sort by fused score and return top_k ───────────────────────
    final_ranked = sorted(
        range(len(candidates)),
        key=lambda i: rrf_scores[i],
        reverse=True
    )[:top_k]

    results = []
    for idx in final_ranked:
        c = candidates[idx]
        results.append({
            "chunk_id"   : c["chunk_id"],
            "text"       : c["text"],
            "source_file": c["source_file"],
            "source_type": c["source_type"],
            "date"       : c["date"],
            "category"   : c["category"],
            "original_file_url": c.get("original_file_url", ""),
            "dense_score": round(c["dense_score"], 4),
            "bm25_score" : round(float(bm25_scores[candidates.index(c)]), 4),
            "fused_score": round(rrf_scores[idx], 6),
        })

    return results


async def _lexical_fallback_search(
    client,
    collection_name: str,
    user_filter: Filter,
    query: str,
    top_k: int,
) -> list[dict]:
    """Search stored payload text when dense vector search is unavailable."""
    points, _ = await client.scroll(
        collection_name=collection_name,
        scroll_filter=user_filter,
        limit=100,
        with_payload=True,
    )

    if not points:
        return []

    candidates = [
        {
            "chunk_id": point.payload.get("chunk_id", str(point.id)),
            "text": point.payload.get("text", ""),
            "source_file": point.payload.get("source_file", "Document"),
            "source_type": point.payload.get("source_type", ""),
            "date": point.payload.get("date", ""),
            "category": point.payload.get("category", ""),
            "original_file_url": point.payload.get("original_file_url", ""),
        }
        for point in points
    ]

    tokenised_corpus = [c["text"].lower().split() for c in candidates]
    bm25 = BM25Okapi(tokenised_corpus)
    bm25_scores = bm25.get_scores(query.lower().split())
    ranked = sorted(range(len(candidates)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]

    return [
        {
            **candidates[idx],
            "dense_score": 0.0,
            "bm25_score": round(float(bm25_scores[idx]), 4),
            "fused_score": round(1.0 / (rank + RRF_K), 6),
        }
        for rank, idx in enumerate(ranked)
    ]
