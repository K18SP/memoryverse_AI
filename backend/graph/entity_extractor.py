"""
Entity Extractor
────────────────
Uses Mistral (via Ollama) to extract structured entities from each chunk.

For every chunk it returns:
  {
    "skills"      : ["Python", "XGBoost", "Data Analysis"],
    "tools"       : ["Jupyter", "Pandas", "Scikit-learn"],
    "organizations": ["Kody Technolab", "Coursera"],
    "roles"       : ["Data Scientist", "ML Engineer"],
    "topics"      : ["Machine Learning", "Classification"],
    "relations"   : [
        {"from": "Python", "to": "XGBoost", "type": "USED_WITH"},
        {"from": "Kody Technolab", "to": "Data Scientist", "type": "EMPLOYED_AS"},
    ]
  }

These become nodes and edges in the Knowledge Graph.
"""

import json
import httpx

EXTRACT_PROMPT = """You are an expert at extracting structured information from academic and professional documents.

Extract the following from the text below:
- skills: programming languages, technical skills, frameworks
- tools: software tools, platforms, libraries  
- organizations: companies, universities, online platforms
- roles: job titles, positions, designations
- topics: subject areas, domains, fields of study
- relations: meaningful connections between extracted entities

Respond ONLY with valid JSON matching this exact structure (no markdown, no explanation):
{
  "skills": [],
  "tools": [],
  "organizations": [],
  "roles": [],
  "topics": [],
  "relations": [{"from": "entity1", "to": "entity2", "type": "RELATION_TYPE"}]
}

Relation types to use:
  USED_WITH, USED_IN, VALIDATES_SKILL, EMPLOYED_AT, STUDIED_AT,
  COMPLETED_AT, LEADS_TO, PART_OF, BUILT_WITH

Text to analyze:
"""


async def extract_entities(text: str) -> dict:
    """
    Extract entities and relations from a single text chunk.
    Returns structured dict with skills, tools, orgs, roles, topics, relations.
    """
    preview = text[:800]   # enough context without overloading the model

    empty_result = {
        "skills"       : [],
        "tools"        : [],
        "organizations": [],
        "roles"        : [],
        "topics"       : [],
        "relations"    : [],
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model" : "mistral",
                    "prompt": f"{EXTRACT_PROMPT}{preview}",
                    "stream": False,
                },
            )
            raw = response.json().get("response", "").strip()

            # Extract JSON block from response
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start == -1 or end <= start:
                return empty_result

            result = json.loads(raw[start:end])

            # Normalise — ensure all keys exist and are lists
            return {
                "skills"       : _clean_list(result.get("skills", [])),
                "tools"        : _clean_list(result.get("tools", [])),
                "organizations": _clean_list(result.get("organizations", [])),
                "roles"        : _clean_list(result.get("roles", [])),
                "topics"       : _clean_list(result.get("topics", [])),
                "relations"    : _clean_relations(result.get("relations", [])),
            }

    except (json.JSONDecodeError, Exception):
        return empty_result


def _clean_list(items: list) -> list[str]:
    """Ensure list contains only non-empty strings."""
    return [str(i).strip() for i in items if i and str(i).strip()]


def _clean_relations(relations: list) -> list[dict]:
    """Ensure relations have from/to/type fields."""
    clean = []
    for r in relations:
        if isinstance(r, dict):
            f = str(r.get("from", "")).strip()
            t = str(r.get("to",   "")).strip()
            k = str(r.get("type", "RELATED_TO")).strip()
            if f and t:
                clean.append({"from": f, "to": t, "type": k})
    return clean


async def extract_entities_batch(texts: list[str]) -> list[dict]:
    """Extract entities from multiple chunks sequentially."""
    import asyncio
    results = []
    for text in texts:
        result = await extract_entities(text)
        results.append(result)
        await asyncio.sleep(0.1)   # small delay to avoid overwhelming Ollama
    return results