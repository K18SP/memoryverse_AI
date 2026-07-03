"""
Gap Analyst
───────────
Compares a student's extracted skills against a target job role.

Workflow:
  1. Fetch all skill/tool nodes from the user's knowledge graph
  2. Accept a target role + optional job description from user
  3. Ask Mistral to compare and identify gaps
  4. Return structured gap report with recommendations

Output:
  {
    "current_skills"    : [...],
    "required_skills"   : [...],
    "matching_skills"   : [...],
    "missing_skills"    : [...],
    "match_percentage"  : 73,
    "recommendations"   : [
        {
          "skill"   : "Docker",
          "reason"  : "Required in 89% of ML Engineer roles",
          "resource": "Play with Docker — free browser-based lab"
        }
    ],
    "radar_data"        : [...]   ← for frontend chart
  }
"""

import json
import httpx
from backend.graph.knowledge_graph import get_graph


async def analyse_gap(
    user_id    : str,
    target_role: str,
    job_description: str = "",
) -> dict:
    """
    Run gap analysis for a user against a target role.

    Args:
        user_id        : user whose graph to analyse
        target_role    : e.g. "ML Engineer", "Data Scientist"
        job_description: optional raw JD text for more accuracy
    """

    # ── Step 1: Extract current skills from knowledge graph ────────────────
    graph = get_graph(user_id)

    current_skills = []
    current_tools  = []

    for node_id, data in graph.nodes(data=True):
        if data.get("node_type") == "skill":
            current_skills.append(data.get("label", ""))
        elif data.get("node_type") == "tool":
            current_tools.append(data.get("label", ""))

    all_current = list(set(current_skills + current_tools))

    if not all_current:
        return {
            "error"  : "No skills found in your knowledge graph. "
                       "Please upload documents and build the graph first.",
            "current_skills": [],
        }

    # ── Step 2: Ask Mistral for gap analysis ───────────────────────────────
    jd_section = f"\nJob Description:\n{job_description[:1000]}" if job_description else ""

    prompt = f"""You are a career coach AI analysing a student's skill gap.

Target Role: {target_role}
{jd_section}

Student's Current Skills and Tools:
{', '.join(all_current)}

Perform a detailed gap analysis. Respond ONLY with valid JSON matching this exact structure:
{{
  "required_skills": ["skill1", "skill2"],
  "matching_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "match_percentage": 70,
  "recommendations": [
    {{
      "skill": "skill_name",
      "reason": "why this skill matters for the role",
      "resource": "specific free resource to learn it",
      "time_weeks": 2
    }}
  ],
  "radar_data": [
    {{"axis": "Machine Learning", "current": 80, "required": 90}},
    {{"axis": "Data Engineering", "current": 40, "required": 75}},
    {{"axis": "MLOps & Deployment", "current": 20, "required": 70}},
    {{"axis": "Statistics", "current": 60, "required": 85}},
    {{"axis": "Programming", "current": 85, "required": 90}},
    {{"axis": "Communication", "current": 50, "required": 65}}
  ],
  "overall_readiness": "You are 70% ready for this role. Your Python and ML foundations are strong, but you need to build MLOps and deployment skills."
}}"""

    empty_result = {
        "current_skills"  : all_current,
        "required_skills" : [],
        "matching_skills" : [],
        "missing_skills"  : [],
        "match_percentage": 0,
        "recommendations" : [],
        "radar_data"      : [],
        "overall_readiness": "Analysis unavailable.",
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={
                    "model" : "mistral",
                    "prompt": prompt,
                    "stream": False,
                },
            )
            raw = response.json().get("response", "").strip()

            # Extract JSON
            start = raw.find("{")
            end   = raw.rfind("}") + 1
            if start == -1 or end <= start:
                return {**empty_result, "current_skills": all_current}

            result = json.loads(raw[start:end])

            return {
                "current_skills"   : all_current,
                "required_skills"  : result.get("required_skills",  []),
                "matching_skills"  : result.get("matching_skills",  []),
                "missing_skills"   : result.get("missing_skills",   []),
                "match_percentage" : result.get("match_percentage",  0),
                "recommendations"  : result.get("recommendations",  []),
                "radar_data"       : result.get("radar_data",        []),
                "overall_readiness": result.get("overall_readiness", ""),
            }

    except (json.JSONDecodeError, Exception) as e:
        return {**empty_result, "error": str(e)}