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


def _get_user_skills(user_id: str) -> list[str]:
    graph = get_graph(user_id)
    return sorted({
        data.get("label", "")
        for _, data in graph.nodes(data=True)
        if data.get("node_type") in ("skill", "tool", "topic")
        and data.get("label", "")
    })


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

    skills = _get_user_skills(user_id)
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

    fallback = _fallback_question(
        skills=skills,
        context=context,
        question_type=question_type,
        difficulty=difficulty,
    )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model":"mistral", "prompt":prompt, "stream":False},
            )
            response.raise_for_status()
            raw    = response.json().get("response", "").strip()
            start  = raw.find("{")
            end    = raw.rfind("}") + 1
            if start == -1 or end <= start:
                return fallback
            result = json.loads(raw[start:end])

            return {
                "question"             : result.get("question", ""),
                "what_interviewer_wants": result.get("what_interviewer_wants", ""),
                "tips"                 : result.get("tips", ""),
                "type"                 : question_type,
                "difficulty"           : difficulty,
                "mode"                 : "ai_enriched",
            }

    except Exception:
        return fallback


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
    fallback = _fallback_evaluation(question, answer, context)

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
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model":"mistral", "prompt":prompt, "stream":False},
            )
            response.raise_for_status()
            raw    = response.json().get("response", "").strip()
            start  = raw.find("{")
            end    = raw.rfind("}") + 1
            if start == -1 or end <= start:
                return fallback
            result = json.loads(raw[start:end])

            return {
                "score"         : result.get("score", 0),
                "star_breakdown": result.get("star_breakdown", {}),
                "strengths"     : result.get("strengths",    []),
                "improvements"  : result.get("improvements", []),
                "ideal_answer"  : result.get("ideal_answer", ""),
                "overall"       : result.get("overall",      ""),
                "mode"          : "ai_enriched",
            }

    except Exception:
        return fallback


def _fallback_question(
    skills: list[str],
    context: str,
    question_type: str,
    difficulty: str,
) -> dict:
    primary_skill = skills[0] if skills else "your strongest technical skill"
    second_skill = skills[1] if len(skills) > 1 else "your project work"

    if question_type == "behavioral":
        question = (
            f"Tell me about a time you used {primary_skill} to solve a difficult problem. "
            "What was the situation, what action did you take, and what was the result?"
        )
        wants = "A clear STAR answer with measurable impact and a reflection on what you learned."
    elif question_type == "project":
        question = (
            f"Walk me through a project or document in your profile where {primary_skill} "
            f"and {second_skill} were important. What tradeoffs did you make?"
        )
        wants = "Specific project context, technical decisions, constraints, and outcomes."
    else:
        question = (
            f"How would you explain your experience with {primary_skill}, and how did you "
            "apply it in the work shown in your uploaded documents?"
        )
        wants = "Ground the answer in real evidence from the profile, not only definitions."

    if difficulty == "hard":
        question += " Include limitations, alternatives, and how you would improve it today."

    return {
        "question": question,
        "what_interviewer_wants": wants,
        "tips": "Use one real example from your uploaded profile and end with a measurable result.",
        "type": question_type,
        "difficulty": difficulty,
        "mode": "instant_profile_based",
    }


def _fallback_evaluation(question: str, answer: str, context: str) -> dict:
    words = [w for w in answer.split() if w.strip()]
    answer_lower = answer.lower()

    has_situation = any(k in answer_lower for k in ["when", "during", "while", "project", "internship"])
    has_task = any(k in answer_lower for k in ["needed", "goal", "task", "responsible", "objective"])
    has_action = any(k in answer_lower for k in ["built", "used", "created", "implemented", "analysed", "designed"])
    has_result = any(k in answer_lower for k in ["result", "improved", "learned", "achieved", "completed", "%"])

    base = min(85, 35 + len(words))
    score = base
    score += 5 if has_situation else -5
    score += 5 if has_task else -5
    score += 5 if has_action else -5
    score += 5 if has_result else -5
    score = max(20, min(95, score))

    def part_score(present: bool) -> int:
        return 80 if present else 45

    return {
        "score": score,
        "star_breakdown": {
            "situation": {
                "score": part_score(has_situation),
                "feedback": "Sets context clearly." if has_situation else "Add the background: project, course, internship, or challenge.",
            },
            "task": {
                "score": part_score(has_task),
                "feedback": "Explains your responsibility." if has_task else "State your specific goal or responsibility.",
            },
            "action": {
                "score": part_score(has_action),
                "feedback": "Describes what you did." if has_action else "Include concrete tools, methods, or decisions you used.",
            },
            "result": {
                "score": part_score(has_result),
                "feedback": "Includes an outcome." if has_result else "End with measurable impact, learning, or final result.",
            },
        },
        "strengths": [
            "Your answer is grounded enough to start a real interview response.",
            "You attempted to connect your experience to the question.",
        ],
        "improvements": [
            "Use a tighter STAR structure.",
            "Mention one specific skill, tool, document, or project from your profile.",
            "Add a result such as accuracy, time saved, certificate earned, or learning outcome.",
        ],
        "ideal_answer": (
            "A strong answer should name the situation, your responsibility, the exact actions "
            "you took with tools or skills, and the final measurable result."
        ),
        "overall": "This instant evaluation checks structure and specificity. For a stronger score, make the answer more concrete and evidence-backed.",
        "mode": "instant_profile_based",
    }
