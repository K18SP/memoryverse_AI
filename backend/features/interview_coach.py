"""
Interview Coach
───────────────
Generates personalised interview questions based on the
student's actual documents, then evaluates their answers.

Two endpoints:
  POST /interview/question  → generate a question from their docs
  POST /interview/evaluate  → score their answer + give feedback

Questions are grounded in real content — not generic.
e.g. "Walk me through why you chose XGBoost over linear models
      in your world_cup_predictions project."
"""

import json
import httpx
from backend.graph.knowledge_graph import get_graph
from backend.vector_store.qdrant_client import get_qdrant_client
from backend.config import get_settings
from qdrant_client.models import Filter, FieldCondition, MatchValue


async def _get_user_context(user_id: str) -> str:
    """Build a summary of the user's documents for the coach prompt."""
    settings = get_settings()
    client   = get_qdrant_client()

    try:
        results, _ = await client.scroll(
            collection_name = settings.qdrant_collection,
            scroll_filter   = Filter(
                must=[FieldCondition(
                    key  ="user_id",
                    match=MatchValue(value=user_id)
                )]
            ),
            limit       = 20,
            with_payload= True,
        )

        if not results:
            return "No documents found."

        # Take first 5 chunks as context
        snippets = [r.payload["text"][:300] for r in results[:5]]
        return "\n\n---\n\n".join(snippets)

    except Exception:
        return "Document context unavailable."


async def generate_question(
    user_id      : str,
    question_type: str = "technical",
    difficulty   : str = "medium",
) -> dict:
    """
    Generate one personalised interview question.

    Args:
        user_id       : whose documents to base the question on
        question_type : "technical" | "behavioral" | "project"
        difficulty    : "easy" | "medium" | "hard"

    Returns:
        {"question": str, "context": str, "tips": str, "type": str}
    """
    context = await _get_user_context(user_id)

    # Also get skill nodes from graph
    graph  = get_graph(user_id)
    skills = [
        data.get("label", "")
        for _, data in graph.nodes(data=True)
        if data.get("node_type") in ("skill", "tool")
    ]
    skills_str = ", ".join(skills[:15]) if skills else "general skills"

    type_instructions = {
        "technical" : "Ask a deep technical question about a specific skill or tool they used.",
        "behavioral": "Ask a behavioral question using STAR format about a challenge they faced.",
        "project"   : "Ask about a specific project — their decisions, tradeoffs, and results.",
    }

    difficulty_instructions = {
        "easy"  : "Keep it straightforward, suitable for a fresher.",
        "medium": "Requires some depth and reasoning.",
        "hard"  : "Requires expert-level reasoning and specific technical detail.",
    }

    prompt = f"""You are an expert technical interviewer.
Generate ONE personalised interview question based on this candidate's actual work.

Candidate's Skills: {skills_str}

Sample from their documents:
{context[:1000]}

Question Type: {question_type} — {type_instructions.get(question_type, '')}
Difficulty: {difficulty} — {difficulty_instructions.get(difficulty, '')}

Respond ONLY with valid JSON:
{{
  "question": "The interview question here",
  "what_interviewer_wants": "What a good answer should cover",
  "tips": "One sentence tip for answering this well"
}}"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model":"mistral", "prompt":prompt, "stream":False},
            )
            raw    = response.json().get("response", "").strip()
            start  = raw.find("{")
            end    = raw.rfind("}") + 1
            result = json.loads(raw[start:end])

            return {
                "question"             : result.get("question", ""),
                "what_interviewer_wants": result.get("what_interviewer_wants", ""),
                "tips"                 : result.get("tips", ""),
                "type"                 : question_type,
                "difficulty"           : difficulty,
            }

    except Exception as e:
        return {
            "question"  : "Tell me about your most challenging technical project.",
            "tips"      : "Use the STAR format: Situation, Task, Action, Result.",
            "type"      : question_type,
            "difficulty": difficulty,
            "error"     : str(e),
        }


async def evaluate_answer(
    question: str,
    answer  : str,
    user_id : str,
) -> dict:
    """
    Score and give feedback on a candidate's interview answer.

    Returns:
        {
          "score"         : 75,        # out of 100
          "star_breakdown": {...},     # STAR format scoring
          "strengths"     : [...],
          "improvements"  : [...],
          "ideal_answer"  : str,       # what a great answer looks like
          "overall"       : str,
        }
    """
    context = await _get_user_context(user_id)

    prompt = f"""You are an expert interview coach evaluating a candidate's answer.

Question: {question}

Candidate's Answer: {answer}

Context from their documents (use this to check if they referenced real work):
{context[:500]}

Evaluate the answer and respond ONLY with valid JSON:
{{
  "score": 75,
  "star_breakdown": {{
    "situation" : {{"score": 80, "feedback": "..."}},
    "task"      : {{"score": 70, "feedback": "..."}},
    "action"    : {{"score": 75, "feedback": "..."}},
    "result"    : {{"score": 60, "feedback": "..."}}
  }},
  "strengths"   : ["strength 1", "strength 2"],
  "improvements": ["improvement 1", "improvement 2"],
  "ideal_answer": "A great answer would include...",
  "overall"     : "Overall feedback in 2 sentences."
}}"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model":"mistral", "prompt":prompt, "stream":False},
            )
            raw    = response.json().get("response", "").strip()
            start  = raw.find("{")
            end    = raw.rfind("}") + 1
            result = json.loads(raw[start:end])

            return {
                "score"         : result.get("score", 0),
                "star_breakdown": result.get("star_breakdown", {}),
                "strengths"     : result.get("strengths",    []),
                "improvements"  : result.get("improvements", []),
                "ideal_answer"  : result.get("ideal_answer", ""),
                "overall"       : result.get("overall",      ""),
            }

    except Exception as e:
        return {"score": 0, "error": str(e),
                "overall": "Evaluation failed. Please try again."}