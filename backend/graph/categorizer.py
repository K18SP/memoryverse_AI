"""
AI Categorizer
──────────────
Uses Claude to assign each document chunk to a category
from our fixed taxonomy. Returns category + confidence.

Taxonomy:
  Education    → Degree | Online Course | Workshop | Bootcamp
  Experience   → Internship | Full-time | Freelance | Research
  Projects     → Academic | Personal | Open Source | Hackathon
  Skills       → Technical | Soft | Domain-specific
  Achievements → Award | Publication | Recognition
"""

import json
import anthropic
from backend.config import get_settings

TAXONOMY = {
    "Education"   : ["Degree", "Online Course", "Workshop", "Bootcamp"],
    "Experience"  : ["Internship", "Full-time", "Freelance", "Research"],
    "Projects"    : ["Academic", "Personal", "Open Source", "Hackathon"],
    "Skills"      : ["Technical", "Soft", "Domain-specific"],
    "Achievements": ["Award", "Publication", "Recognition"],
    "Other"       : ["Miscellaneous"],
}

CATEGORY_PROMPT = """You are a document classifier for a student portfolio system.
Classify the following text into exactly one category and subcategory.

Taxonomy:
- Education: Degree, Online Course, Workshop, Bootcamp
- Experience: Internship, Full-time, Freelance, Research
- Projects: Academic, Personal, Open Source, Hackathon
- Skills: Technical, Soft, Domain-specific
- Achievements: Award, Publication, Recognition
- Other: Miscellaneous

Respond ONLY with valid JSON, no explanation, no markdown:
{"category": "Education", "subcategory": "Online Course", "confidence": 0.95}"""


async def categorize_chunk(text: str) -> dict:
    """
    Classify a single text chunk.

    Returns:
        {"category": str, "subcategory": str, "confidence": float}
    """
    settings = get_settings()
    client   = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Only send first 500 chars — enough for classification
    preview  = text[:500]

    response = client.messages.create(
        model      = "claude-haiku-20240307",   # fast + cheap for classification
        max_tokens = 100,
        messages   = [{
            "role"   : "user",
            "content": f"{CATEGORY_PROMPT}\n\nText to classify:\n{preview}"
        }],
    )

    raw = response.content[0].text.strip()

    try:
        result = json.loads(raw)
        return {
            "category"   : result.get("category", "Other"),
            "subcategory": result.get("subcategory", "Miscellaneous"),
            "confidence" : float(result.get("confidence", 0.5)),
        }
    except (json.JSONDecodeError, ValueError):
        return {
            "category"   : "Other",
            "subcategory": "Miscellaneous",
            "confidence" : 0.0,
        }


async def categorize_chunks(texts: list[str]) -> list[dict]:
    """Categorize multiple chunks. Returns list in same order."""
    import asyncio
    tasks   = [categorize_chunk(t) for t in texts]
    results = await asyncio.gather(*tasks)
    return list(results)