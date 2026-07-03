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
    query_vector = await generate_single_embedding(query)

    # Filter to only this user's documents
    user_filter  = Filter(
        must=[FieldCondition(
            key="user_id",
            match=MatchValue(value=user_id)
        )]
    )

    dense_results = await client.search(
        collection_name = settings.qdrant_collection,
        query_vector    = ("dense", query_vector),
        query_filter    = user_filter,
        limit           = top_k * 3,       # fetch more, rerank later
        with_payload    = True,
    )

    if not dense_results:
        return []

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
            "dense_score": hit.score,
        }
        for hit in dense_results
    ]

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
            "dense_score": round(c["dense_score"], 4),
            "bm25_score" : round(float(bm25_scores[candidates.index(c)]), 4),
            "fused_score": round(rrf_scores[idx], 6),
        })

    return results