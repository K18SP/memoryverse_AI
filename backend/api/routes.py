"""
API Routes — Block 1B
Ingestion now goes all the way:
  upload → extract → chunk → embed → upsert to Qdrant
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
import uuid
from datetime import datetime

from backend.ingestion.router import detect_and_extract
from backend.embeddings.chunker import chunk_text
from backend.embeddings.generator import generate_embeddings
from backend.vector_store.qdrant_client import upsert_chunks, delete_user_documents
from backend.vector_store.schema import DocChunk
from backend.config import get_settings
from backend.retrieval.rag_chain import rag_query
from backend.graph.categorizer import categorize_chunks

from backend.graph.entity_extractor import extract_entities_batch
from backend.graph.knowledge_graph import (
    add_document_node,
    add_entities_to_graph,
    get_graph_for_frontend,
    get_node_neighbours,
    reset_graph,
)

from backend.features.gap_analyst import analyse_gap
from backend.features.interview_coach import generate_question, evaluate_answer
from backend.storage.file_store import save_original_file, resolve_original_file

router = APIRouter()


@router.post("/ingest", summary="Upload a document or GitHub URL for indexing")
async def ingest_document(
    file      : Optional[UploadFile] = File(None),
    github_url: Optional[str]        = Form(None),
    user_id   : str                  = Form(...),
    date      : Optional[str]        = Form(None),
):
    settings = get_settings()
    doc_id = str(uuid.uuid4())
    original_file_meta = {}

    # ── Validate file size ─────────────────────────────────────────────────
    if file:
        import io
        raw = await file.read()
        size_mb = len(raw) / (1024 * 1024)
        if size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                413,
                f"File too large: {size_mb:.1f} MB. Max: {settings.max_upload_size_mb} MB",
            )
        original_file_meta = save_original_file(
            user_id=user_id,
            doc_id=doc_id,
            filename=file.filename or "uploaded_file",
            raw_bytes=raw,
        )
        file.file = io.BytesIO(raw)

    # ── Step 1: Extract text ───────────────────────────────────────────────
    extracted = await detect_and_extract(file=file, github_url=github_url)

    timestamp = date or datetime.utcnow().strftime("%Y-%m-%d")

    # ── Step 2: Chunk the text ─────────────────────────────────────────────
    chunks = chunk_text(extracted["text"])

    if not chunks:
        raise HTTPException(422, "No text could be extracted from this document.")

    # ── Step 3: Generate embeddings ────────────────────────────────────────
    try:
        texts    = [c["text"] for c in chunks]
        vectors  = await generate_embeddings(texts)
    except Exception as e:
        # If OpenAI key not set yet, skip embedding and return extraction result
        return JSONResponse({
            "status"     : "extracted_only",
            "warning"    : f"Embedding skipped: {str(e)}",
            "doc_id"     : doc_id,
            "user_id"    : user_id,
            "source_type": extracted["source_type"],
            "source_file": extracted["source_file"],
            "original_file_url": original_file_meta.get("original_file_url"),
            "date"       : timestamp,
            "char_count" : len(extracted["text"]),
            "chunk_count": len(chunks),
            "preview"    : extracted["text"][:300],
        })

    # ── Step 4: Build DocChunk payloads ────────────────────────────────────
    chunks_with_vectors = []
    for chunk, vector in zip(chunks, vectors):
        doc_chunk = DocChunk(
            doc_id      = doc_id,
            user_id     = user_id,
            text        = chunk["text"],
            chunk_index = chunk["chunk_index"],
            token_count = chunk["token_count"],
            source_type = extracted["source_type"],
            source_file = extracted["source_file"],
            date        = timestamp,
            original_file_url= original_file_meta.get("original_file_url"),
        )
        chunks_with_vectors.append({
            "payload": doc_chunk.to_payload(),
            "vector" : vector,
        })

    # ── Step 5: Upsert to Qdrant ───────────────────────────────────────────
    try:
        upserted = await upsert_chunks(chunks_with_vectors)
        status   = "indexed"
    except Exception as e:
        upserted = 0
        status   = f"embedding_done_qdrant_failed: {str(e)}"

    return JSONResponse({
        "status"     : status,
        "doc_id"     : doc_id,
        "user_id"    : user_id,
        "source_type": extracted["source_type"],
        "source_file": extracted["source_file"],
        "original_file_url": original_file_meta.get("original_file_url"),
        "date"       : timestamp,
        "char_count" : len(extracted["text"]),
        "chunk_count": len(chunks),
        "upserted"   : upserted,
        "preview"    : extracted["text"][:300],
    })


@router.get("/health/ingestion")
async def ingestion_health():
    checks = {}
    try:
        import pypdf
        checks["pypdf"] = "ok"
    except ImportError as e:
        checks["pypdf"] = str(e)

    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        checks["tesseract"] = "ok"
    except Exception as e:
        checks["tesseract"] = f"warning: {e}"

    try:
        import tiktoken
        checks["tiktoken"] = "ok"
    except ImportError as e:
        checks["tiktoken"] = str(e)

    try:
        import openai
        checks["openai"] = "ok"
    except ImportError as e:
        checks["openai"] = str(e)

    try:
        from docx import Document
        checks["python_docx"] = "ok"
    except ImportError as e:
        checks["python_docx"] = str(e)

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "checks": checks,
    }


@router.get("/files/{user_id}/{doc_id}/{filename:path}", summary="Open an original uploaded file")
async def get_original_file(user_id: str, doc_id: str, filename: str):
    path = resolve_original_file(user_id, doc_id, filename)
    return FileResponse(
        path,
        filename=path.name,
        media_type="application/octet-stream",
    )


@router.delete("/documents/{user_id}", summary="Clear all indexed documents for a user")
async def clear_user_documents(user_id: str):
    """
    Clears the demo user's vector index and in-memory graph.
    Useful during hackathon demos when repeated test uploads create duplicates.
    """
    try:
        await delete_user_documents(user_id)
        reset_graph(user_id)
    except Exception as e:
        raise HTTPException(500, f"Could not clear documents: {str(e)}")

    return JSONResponse({
        "status": "cleared",
        "user_id": user_id,
    })

@router.post("/search", summary="Ask a natural language question about your documents")
async def search_documents(
    query  : str = Form(...),
    user_id: str = Form(...),
    top_k  : int = Form(5),
):
    """
    RAG-powered semantic search.
    Retrieves relevant chunks and generates a cited answer using Claude.
    """
    if not query.strip():
        raise HTTPException(400, "Query cannot be empty.")

    result = await rag_query(query=query, user_id=user_id, top_k=top_k)

    return JSONResponse({
        "query"     : result["query"],
        "answer"    : result["answer"],
        "confidence": result["confidence"],
        "sources"   : result["sources"],
    })


@router.post("/categorize", summary="Categorize an already-ingested document by doc_id")
async def categorize_document(
    texts  : list[str],
    user_id: str = Form(...),
):
    """Batch categorize a list of text chunks."""
    if not texts:
        raise HTTPException(400, "No texts provided.")

    categories = await categorize_chunks(texts)
    return JSONResponse({"categories": categories})

@router.get("/graph/{user_id}", summary="Get full knowledge graph for a user")
async def get_knowledge_graph(user_id: str):
    """
    Returns D3.js-compatible graph data.
    Frontend uses this to render the interactive knowledge graph.
    """
    graph_data = get_graph_for_frontend(user_id)
    return JSONResponse(graph_data)


@router.get("/graph/{user_id}/node/{node_id:path}", summary="Get neighbours of a node")
async def get_node_details(user_id: str, node_id: str):
    """
    Returns all connections of a specific node.
    Called when user clicks a node in the frontend graph.
    """
    neighbours = get_node_neighbours(user_id, node_id)
    return JSONResponse(neighbours)


@router.post("/graph/{user_id}/build", summary="Build knowledge graph from ingested documents")
async def build_knowledge_graph(user_id: str):
    """
    Fetches all chunks for this user from Qdrant,
    runs entity extraction on each, and builds the graph.
    Call this after ingesting documents.
    """
    from backend.vector_store.qdrant_client import get_qdrant_client
    from backend.config import get_settings
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    settings = get_settings()
    client   = get_qdrant_client()
    reset_graph(user_id)

    # Fetch all chunks for this user
    results, _ = await client.scroll(
        collection_name = settings.qdrant_collection,
        scroll_filter   = Filter(
            must=[FieldCondition(
                key  ="user_id",
                match=MatchValue(value=user_id)
            )]
        ),
        limit      = 100,
        with_payload= True,
    )

    if not results:
        return JSONResponse({
            "status" : "no_documents",
            "message": "No documents found. Please ingest documents first."
        })

    # Group chunks by doc_id
    docs: dict[str, list] = {}
    for point in results:
        doc_id = point.payload["doc_id"]
        if doc_id not in docs:
            docs[doc_id] = []
        docs[doc_id].append(point.payload)

    total_entities = 0
    total_relations = 0

    for doc_id, chunks in docs.items():
        # Add document node
        first_chunk = chunks[0]
        add_document_node(
            user_id    = user_id,
            doc_id     = doc_id,
            source_file= first_chunk["source_file"],
            source_type= first_chunk["source_type"],
            date       = first_chunk["date"],
            category   = first_chunk.get("category", ""),
            original_file_url= first_chunk.get("original_file_url"),
        )

        # Extract entities from all chunks of this document
        texts    = [c["text"] for c in chunks]
        entities_list = await extract_entities_batch(texts)

        # Merge all entities from all chunks
        merged = {
            "skills"       : [],
            "tools"        : [],
            "organizations": [],
            "roles"        : [],
            "topics"       : [],
            "relations"    : [],
        }
        for ent in entities_list:
            for key in merged:
                merged[key].extend(ent.get(key, []))

        # Deduplicate
        for key in ["skills", "tools", "organizations", "roles", "topics"]:
            merged[key] = list(set(merged[key]))

        # Add to graph
        add_entities_to_graph(user_id, doc_id, merged)

        total_entities += sum(
            len(merged[k]) for k in ["skills","tools","organizations","roles","topics"]
        )
        total_relations += len(merged["relations"])

    graph_data = get_graph_for_frontend(user_id)

    return JSONResponse({
        "status"         : "built",
        "documents"      : len(docs),
        "total_entities" : total_entities,
        "total_relations": total_relations,
        "graph_summary"  : {
            "nodes": graph_data["node_count"],
            "edges": graph_data["edge_count"],
        }
    })

# ── Gap Analyst ────────────────────────────────────────────────────────────

@router.post("/gap-analysis", summary="Analyse skill gaps vs a target role")
async def gap_analysis(
    user_id        : str = Form(...),
    target_role    : str = Form(...),
    job_description: str = Form(""),
):
    """
    Compare user's current skills against a target job role.
    Returns match percentage, missing skills, and learning recommendations.
    """
    result = await analyse_gap(
        user_id         = user_id,
        target_role     = target_role,
        job_description = job_description,
    )
    return JSONResponse(result)


# ── Interview Coach ────────────────────────────────────────────────────────

@router.post("/interview/question", summary="Generate a personalised interview question")
async def get_interview_question(
    user_id      : str = Form(...),
    question_type: str = Form("technical"),
    difficulty   : str = Form("medium"),
):
    """
    Generate one interview question grounded in the user's actual documents.
    question_type: technical | behavioral | project
    difficulty   : easy | medium | hard
    """
    result = await generate_question(
        user_id       = user_id,
        question_type = question_type,
        difficulty    = difficulty,
    )
    return JSONResponse(result)


@router.post("/interview/evaluate", summary="Evaluate an interview answer")
async def evaluate_interview_answer(
    user_id : str = Form(...),
    question: str = Form(...),
    answer  : str = Form(...),
):
    """
    Score the candidate's answer and provide STAR-format feedback.
    """
    result = await evaluate_answer(
        question = question,
        answer   = answer,
        user_id  = user_id,
    )
    return JSONResponse(result)
