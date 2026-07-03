"""
RAG Chain — FREE version using Ollama (local LLM, no API key needed)
Model: Mistral 7B running locally via Ollama
"""

import httpx
from backend.retrieval.hybrid_search import hybrid_search

MIN_CONFIDENCE = 0.015

SYSTEM_PROMPT = """You are MemoryVerse AI, a personal knowledge assistant.
Answer ONLY using the provided document context.
Always mention which document your answer comes from.
If context is insufficient, say: "I don't have enough information in your documents."
Be concise and professional."""


async def rag_query(
    query  : str,
    user_id: str,
    top_k  : int = 5,
) -> dict:

    # ── Step 1: Retrieve relevant chunks ───────────────────────────────────
    chunks = await hybrid_search(query=query, user_id=user_id, top_k=top_k)

    if not chunks:
        return {
            "answer"    : "No documents found. Please upload some documents first.",
            "sources"   : [],
            "confidence": 0.0,
            "query"     : query,
        }

    best_score = chunks[0]["fused_score"]

    # ── Step 2: Build context ──────────────────────────────────────────────
    context_parts = []
    for i, chunk in enumerate(chunks, start=1):
        context_parts.append(
            f"[Document {i}: {chunk['source_file']}]\n{chunk['text']}"
        )
    context = "\n\n---\n\n".join(context_parts)

    # ── Step 3: Call Ollama ────────────────────────────────────────────────
    prompt = f"""{SYSTEM_PROMPT}

Documents:
{context}

Question: {query}

Answer (cite document names):"""

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model" : "mistral",
                    "prompt": prompt,
                    "stream": False,
                }
            )
            data   = response.json()
            answer = data.get("response", "No response from model.")
    except Exception as e:
        import traceback
        answer = f"LLM unavailable: {str(e)} | {traceback.format_exc()}. Retrieved chunks are in sources below."

    # ── Step 4: Return ─────────────────────────────────────────────────────
    return {
        "answer"    : answer,
        "sources"   : [
            {
                "document"   : c["source_file"],
                "type"       : c["source_type"],
                "date"       : c["date"],
                "preview"    : c["text"][:150] + "...",
                "fused_score": c["fused_score"],
                "dense_score": c["dense_score"],
                "bm25_score" : c["bm25_score"],
            }
            for c in chunks
        ],
        "confidence": best_score,
        "query"     : query,
    }