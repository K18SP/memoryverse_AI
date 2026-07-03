"""
RAG Chain — FREE version using Ollama (local LLM, no API key needed)
Model: Mistral 7B running locally via Ollama
"""

import re

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
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model" : "mistral",
                    "prompt": prompt,
                    "stream": False,
                }
            )
            response.raise_for_status()
            data   = response.json()
            answer = data.get("response") or _fallback_answer(query, chunks)
            answer_mode = "ai_enriched"
    except Exception:
        answer = _fallback_answer(query, chunks)
        answer_mode = "instant_retrieval"

    # ── Step 4: Return ─────────────────────────────────────────────────────
    return {
        "answer"    : answer,
        "sources"   : [
            {
                "document"   : c["source_file"],
                "type"       : c["source_type"],
                "date"       : c["date"],
                "original_file_url": c.get("original_file_url", ""),
                "preview"    : c["text"][:150] + "...",
                "fused_score": c["fused_score"],
                "dense_score": c["dense_score"],
                "bm25_score" : c["bm25_score"],
            }
            for c in chunks
        ],
        "confidence": best_score,
        "query"     : query,
        "answer_mode": answer_mode,
    }


def _fallback_answer(query: str, chunks: list[dict]) -> str:
    """Fast grounded answer when the local LLM is unavailable."""
    if not chunks:
        return "No matching documents were found."

    query_lower = query.lower()
    combined_text = "\n".join(chunk.get("text", "") for chunk in chunks)

    doc_names = []
    for chunk in chunks:
        name = chunk.get("source_file", "uploaded document")
        if name not in doc_names:
            doc_names.append(name)

    if any(word in query_lower for word in ["skill", "skills", "technical", "tools", "technologies"]):
        skills = _extract_known_skills(combined_text)
        if skills:
            return (
                "Based on your uploaded documents, your technical skills include: "
                f"{', '.join(skills[:18])}.\n\n"
                f"Evidence found in: {', '.join(doc_names[:3])}."
            )

    if any(word in query_lower for word in ["certificate", "certificates", "certification"]):
        certificate_lines = _extract_topic_lines(
            combined_text,
            ["certificate", "certification", "certified", "course", "specialization"],
        )
        if certificate_lines:
            return (
                "I found these certification-related details:\n"
                + "\n".join(f"- {line}" for line in certificate_lines[:5])
                + f"\n\nEvidence found in: {', '.join(doc_names[:3])}."
            )
        return (
            f"I found certificate-related evidence in: {', '.join(doc_names[:3])}.\n\n"
            + _format_evidence_lines(chunks, max_lines=3)
        )

    if any(word in query_lower for word in ["internship", "internships", "intern"]):
        internship_lines = _extract_topic_lines(
            combined_text,
            ["internship", "intern", "trainee", "company", "worked", "experience"],
        )
        if internship_lines:
            return (
                "Here is what your documents mention about internships or work experience:\n"
                + "\n".join(f"- {line}" for line in internship_lines[:5])
                + f"\n\nEvidence found in: {', '.join(doc_names[:3])}."
            )
        return (
            "I did not find strong internship-specific evidence in the retrieved text. "
            f"The closest matching document is: {', '.join(doc_names[:3])}."
        )

    if any(word in query_lower for word in ["achievement", "achievements", "award", "awards"]):
        achievement_lines = _extract_topic_lines(
            combined_text,
            ["achievement", "award", "rank", "winner", "lead", "completed", "cgpa", "score"],
        )
        if achievement_lines:
            return (
                "I found these achievement-related details:\n"
                + "\n".join(f"- {line}" for line in achievement_lines[:5])
                + f"\n\nEvidence found in: {', '.join(doc_names[:3])}."
            )

    if any(word in query_lower for word in ["academic", "academics", "education", "college", "university", "cgpa"]):
        academic_lines = _extract_topic_lines(
            combined_text,
            ["education", "academic", "college", "university", "cgpa", "engineering", "degree"],
        )
        if academic_lines:
            return (
                "I found these academic details:\n"
                + "\n".join(f"- {line}" for line in academic_lines[:5])
                + f"\n\nEvidence found in: {', '.join(doc_names[:3])}."
            )

    if any(phrase in query_lower for phrase in ["about me", "summary", "profile", "who am i"]):
        summary_lines = _extract_topic_lines(
            combined_text,
            ["profile summary", "summary", "experience", "graduate", "developer", "engineer"],
        )
        if summary_lines:
            return (
                "Here is a concise profile summary from your documents:\n"
                + "\n".join(f"- {line}" for line in summary_lines[:4])
                + f"\n\nEvidence found in: {', '.join(doc_names[:3])}."
            )

    if "resume" in query_lower or "cv" in query_lower:
        resume_docs = [name for name in doc_names if "resume" in name.lower() or "cv" in name.lower()]
        shown_docs = resume_docs or doc_names[:3]
        return (
            f"The most relevant resume/CV document is: {', '.join(shown_docs)}.\n\n"
            + _format_evidence_lines(chunks, max_lines=2)
        )

    if any(word in query_lower for word in ["project", "projects", "built", "portfolio"]):
        project_lines = _extract_project_lines(combined_text)
        if project_lines:
            return (
                "I found these project-related items in your documents:\n"
                + "\n".join(f"- {line}" for line in project_lines[:5])
                + f"\n\nEvidence found in: {', '.join(doc_names[:3])}."
            )

    previews = []
    seen_previews = set()
    for chunk in chunks[:3]:
        preview = chunk.get("text", "").strip().replace("\n", " ")
        preview = re.sub(r"\s+", " ", preview)
        preview_key = preview[:120].lower()
        if preview and preview_key not in seen_previews:
            seen_previews.add(preview_key)
            previews.append(f"- {chunk.get('source_file', 'Document')}: {preview[:220]}")

    return (
        f"Most relevant documents for \"{query}\": {', '.join(doc_names[:3])}.\n\n"
        "Evidence preview:\n" + "\n".join(previews)
    )


def _extract_known_skills(text: str) -> list[str]:
    known = [
        "Python", "Java", "JavaScript", "TypeScript", "HTML", "CSS", "SQL",
        "React", "Node.js", "FastAPI", "Django", "Flask", "Streamlit",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "RAG", "LLM", "LangChain", "LlamaIndex", "Pandas", "NumPy",
        "Matplotlib", "Seaborn", "Scikit-learn", "TensorFlow", "PyTorch",
        "OpenCV", "Git", "GitHub", "Docker", "AWS", "Azure", "GCP",
        "Power BI", "Tableau", "Excel", "Statistics", "Linear Algebra",
        "Probability", "Calculus", "Qdrant", "Hugging Face",
    ]
    found = []
    for skill in known:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(skill) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(skill)
    return _dedupe(found)


def _extract_project_lines(text: str) -> list[str]:
    lines = [re.sub(r"\s+", " ", line).strip(" -•") for line in text.splitlines()]
    project_lines = [
        line for line in lines
        if line and any(word in line.lower() for word in ["project", "built", "developed", "designed", "deployed"])
    ]
    return _dedupe([line[:180] for line in project_lines])


def _format_evidence_lines(chunks: list[dict], max_lines: int = 3) -> str:
    lines = []
    for chunk in chunks:
        preview = re.sub(r"\s+", " ", chunk.get("text", "").strip())
        if preview:
            lines.append(f"- {chunk.get('source_file', 'Document')}: {preview[:220]}")
        if len(lines) >= max_lines:
            break
    return "Evidence preview:\n" + "\n".join(lines)


def _extract_topic_lines(text: str, keywords: list[str]) -> list[str]:
    normalized = re.sub(r"[|]", "\n", text)
    raw_lines = []
    for line in normalized.splitlines():
        raw_lines.extend(re.split(r"(?<=[.!?])\s+", line))

    lines = []
    for line in raw_lines:
        clean = re.sub(r"\s+", " ", line).strip(" -:;")
        if len(clean) < 12:
            continue
        clean_lower = clean.lower()
        if any(keyword in clean_lower for keyword in keywords):
            lines.append(clean[:220])
    return _dedupe(lines)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
