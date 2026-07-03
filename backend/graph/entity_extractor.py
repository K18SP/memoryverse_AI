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
import re
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

    fallback_result = _fallback_extract_entities(text)

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model" : "mistral",
                    "prompt": f"{EXTRACT_PROMPT}{preview}",
                    "stream": False,
                },
            )
            response.raise_for_status()
            raw = response.json().get("response", "").strip()

            # Extract JSON block from response
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start == -1 or end <= start:
                return fallback_result

            result = json.loads(raw[start:end])

            # Normalise — ensure all keys exist and are lists
            llm_result = {
                "skills"       : _clean_list(result.get("skills", [])),
                "tools"        : _clean_list(result.get("tools", [])),
                "organizations": _clean_list(result.get("organizations", [])),
                "roles"        : _clean_list(result.get("roles", [])),
                "topics"       : _clean_list(result.get("topics", [])),
                "relations"    : _clean_relations(result.get("relations", [])),
            }

            return _merge_entity_results(fallback_result, llm_result)

    except (json.JSONDecodeError, Exception):
        return fallback_result


def _fallback_extract_entities(text: str) -> dict:
    """
    Fast deterministic extractor used when the local LLM is unavailable.
    This keeps graph building reliable during demos and hackathon judging.
    """
    known_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "SQL", "HTML", "CSS",
        "Machine Learning", "Deep Learning", "Data Science", "Data Analysis",
        "Statistics", "NLP", "Computer Vision", "React", "Node.js", "FastAPI",
        "Django", "Flask", "Pandas", "NumPy", "Scikit-learn", "TensorFlow",
        "PyTorch", "OpenCV", "Power BI", "Tableau", "Excel", "Git", "GitHub",
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "MongoDB", "PostgreSQL",
    ]
    known_topics = [
        "Artificial Intelligence", "Cloud Computing", "Databases",
        "Software Engineering", "Analytics", "Visualization", "Big Data",
        "Data Engineering", "MLOps", "Web Development",
    ]
    known_roles = [
        "Data Scientist", "Data Analyst", "Software Engineer", "ML Engineer",
        "AI Engineer", "Frontend Developer", "Backend Developer",
        "Full Stack Developer", "Intern", "Research Intern",
    ]

    found_skills = _find_known_terms(text, known_skills)
    found_topics = _find_known_terms(text, known_topics)
    found_roles = _find_known_terms(text, known_roles)

    organizations = []
    org_patterns = [
        r"\bIBM\b",
        r"\bCoursera\b",
        r"\bGoogle\b",
        r"\bMicrosoft\b",
        r"\bAmazon\b",
        r"\bMeta\b",
        r"\bLinkedIn\b",
        r"\bUdemy\b",
        r"\b(edX|NPTEL|IIT|University|College|Institute)\b",
    ]
    for pattern in org_patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            value = match.group(0)
            organizations.append(value.upper() if value.lower() == "ibm" else value)

    relations = []
    for skill in found_skills:
        relations.append({
            "from": "Document",
            "to": skill,
            "type": "VALIDATES_SKILL",
        })

    return {
        "skills": found_skills,
        "tools": [s for s in found_skills if s in {"Git", "GitHub", "Docker", "Excel", "Power BI", "Tableau"}],
        "organizations": _dedupe_preserve_order(organizations),
        "roles": found_roles,
        "topics": found_topics,
        "relations": relations,
    }


def _find_known_terms(text: str, terms: list[str]) -> list[str]:
    found = []
    for term in terms:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(term)
    return _dedupe_preserve_order(found)


def _merge_entity_results(base: dict, extra: dict) -> dict:
    merged = {}
    for key in ["skills", "tools", "organizations", "roles", "topics"]:
        merged[key] = _dedupe_preserve_order(base.get(key, []) + extra.get(key, []))
    merged["relations"] = base.get("relations", []) + extra.get("relations", [])
    return merged


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    clean = []
    for item in items:
        value = str(item).strip()
        key = value.lower()
        if value and key not in seen:
            clean.append(value)
            seen.add(key)
    return clean


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
