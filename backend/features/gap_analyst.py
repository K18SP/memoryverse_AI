"""
Gap Analyst

Compares extracted graph skills against a target role. The feature returns a
deterministic report immediately, then uses the local LLM only as optional
enrichment when it is available.
"""

import json

import httpx

from backend.graph.knowledge_graph import get_graph


ROLE_REQUIREMENTS = {
    "ml engineer": [
        "Python", "Machine Learning", "Deep Learning", "Scikit-learn",
        "TensorFlow", "PyTorch", "Pandas", "NumPy", "Statistics",
        "SQL", "Docker", "MLOps", "Git", "GitHub",
    ],
    "data scientist": [
        "Python", "Data Science", "Machine Learning", "Statistics",
        "Pandas", "NumPy", "Scikit-learn", "SQL", "Data Analysis",
        "Deep Learning", "TensorFlow", "Visualization", "Git",
    ],
    "data analyst": [
        "SQL", "Excel", "Python", "Data Analysis", "Statistics",
        "Power BI", "Tableau", "Visualization", "Pandas",
    ],
    "backend developer": [
        "Python", "Java", "Node.js", "FastAPI", "Django", "Flask",
        "SQL", "PostgreSQL", "MongoDB", "Docker", "Git", "GitHub", "AWS",
    ],
    "full stack developer": [
        "HTML", "CSS", "JavaScript", "TypeScript", "React", "Node.js",
        "Python", "FastAPI", "SQL", "PostgreSQL", "Git", "GitHub", "Docker",
    ],
    "ai research engineer": [
        "Python", "Machine Learning", "Deep Learning", "NLP",
        "Computer Vision", "PyTorch", "TensorFlow", "Statistics",
        "Research", "Data Science", "Git",
    ],
}

DEFAULT_REQUIREMENTS = [
    "Python", "SQL", "Git", "GitHub", "Data Analysis",
    "Communication", "Problem Solving",
]


async def analyse_gap(
    user_id: str,
    target_role: str,
    job_description: str = "",
) -> dict:
    graph = get_graph(user_id)

    current_skills = []
    current_tools = []

    for _, data in graph.nodes(data=True):
        if data.get("node_type") == "skill":
            current_skills.append(data.get("label", ""))
        elif data.get("node_type") == "tool":
            current_tools.append(data.get("label", ""))

    all_current = sorted({s for s in current_skills + current_tools if s})

    if not all_current:
        return {
            "error": "No skills found in your knowledge graph. Please upload documents and build the graph first.",
            "current_skills": [],
        }

    fallback = _build_gap_report(all_current, target_role, job_description)

    prompt = f"""You are a career coach AI analysing a student's skill gap.

Target Role: {target_role}
Job Description: {job_description[:1000] if job_description else "Not provided"}

Student's Current Skills and Tools:
{', '.join(all_current)}

Return ONLY valid JSON with this exact structure:
{{
  "required_skills": [],
  "matching_skills": [],
  "missing_skills": [],
  "match_percentage": 70,
  "recommendations": [
    {{"skill": "skill", "reason": "reason", "resource": "resource", "time_weeks": 2}}
  ],
  "radar_data": [
    {{"axis": "Programming", "current": 80, "required": 90}}
  ],
  "overall_readiness": "short summary"
}}"""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                "http://127.0.0.1:11434/api/generate",
                json={"model": "mistral", "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            raw = response.json().get("response", "").strip()

        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end <= start:
            return fallback

        result = json.loads(raw[start:end])
        return {
            "current_skills": all_current,
            "required_skills": result.get("required_skills") or fallback["required_skills"],
            "matching_skills": result.get("matching_skills") or fallback["matching_skills"],
            "missing_skills": result.get("missing_skills") or fallback["missing_skills"],
            "match_percentage": result.get("match_percentage") or fallback["match_percentage"],
            "recommendations": result.get("recommendations") or fallback["recommendations"],
            "radar_data": result.get("radar_data") or fallback["radar_data"],
            "overall_readiness": result.get("overall_readiness") or fallback["overall_readiness"],
            "analysis_mode": "llm_enriched",
        }
    except Exception:
        return fallback


def _build_gap_report(
    current_skills: list[str],
    target_role: str,
    job_description: str = "",
) -> dict:
    required = list(ROLE_REQUIREMENTS.get(target_role.lower().strip(), DEFAULT_REQUIREMENTS))

    if job_description:
        jd_lower = job_description.lower()
        all_known = DEFAULT_REQUIREMENTS + [
            skill for skills in ROLE_REQUIREMENTS.values() for skill in skills
        ]
        for skill in all_known:
            if skill.lower() in jd_lower and skill not in required:
                required.append(skill)

    current_lookup = {skill.lower(): skill for skill in current_skills}
    matching = []
    missing = []

    for skill in required:
        if skill.lower() in current_lookup:
            matching.append(current_lookup[skill.lower()])
        else:
            missing.append(skill)

    match_percentage = round((len(matching) / max(len(required), 1)) * 100)

    recommendations = [
        {
            "skill": skill,
            "reason": f"{skill} is commonly expected for {target_role} roles and is not strongly evidenced in your uploaded documents yet.",
            "resource": _resource_for_skill(skill),
            "resource_url": _resource_url_for_skill(skill),
            "time_weeks": 2 if skill in {"Git", "GitHub", "SQL", "Excel"} else 4,
        }
        for skill in missing[:5]
    ]

    if match_percentage >= 75:
        readiness = f"You are strongly aligned for {target_role}. Add more project evidence for the missing skills to make your profile interview-ready."
    elif match_percentage >= 45:
        readiness = f"You have a good base for {target_role}, but should add evidence for {', '.join(missing[:3])}."
    else:
        readiness = f"You are early for {target_role}. Start by building proof around {', '.join(missing[:3])}."

    return {
        "current_skills": current_skills,
        "required_skills": required,
        "matching_skills": matching,
        "missing_skills": missing,
        "match_percentage": match_percentage,
        "recommendations": recommendations,
        "radar_data": _build_radar_data(current_skills, required),
        "overall_readiness": readiness,
        "analysis_mode": "deterministic",
    }


def _resource_for_skill(skill: str) -> str:
    resources = {
        "SQL": "Mode SQL Tutorial or Khan Academy SQL",
        "Docker": "Docker Get Started guide",
        "MLOps": "Google MLOps whitepaper and Evidently AI tutorials",
        "TensorFlow": "TensorFlow Core tutorials",
        "PyTorch": "PyTorch official tutorials",
        "Power BI": "Microsoft Learn Power BI path",
        "Tableau": "Tableau Free Training Videos",
        "React": "React official Learn guide",
        "FastAPI": "FastAPI official tutorial",
        "Statistics": "StatQuest Statistics playlist",
    }
    return resources.get(skill, f"Build a small portfolio project using {skill}")


def _resource_url_for_skill(skill: str) -> str:
    urls = {
        "SQL": "https://mode.com/sql-tutorial/",
        "Docker": "https://docs.docker.com/get-started/",
        "MLOps": "https://cloud.google.com/architecture/mlops-continuous-delivery-and-automation-pipelines-in-machine-learning",
        "TensorFlow": "https://www.tensorflow.org/tutorials",
        "PyTorch": "https://pytorch.org/tutorials/",
        "Power BI": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi",
        "Tableau": "https://www.tableau.com/learn/training",
        "React": "https://react.dev/learn",
        "FastAPI": "https://fastapi.tiangolo.com/tutorial/",
        "Statistics": "https://www.youtube.com/user/joshstarmer",
        "Git": "https://www.atlassian.com/git/tutorials",
        "GitHub": "https://docs.github.com/en/get-started",
    }
    return urls.get(skill, "https://www.freecodecamp.org/learn/")


def _build_radar_data(current_skills: list[str], required: list[str]) -> list[dict]:
    current = {skill.lower() for skill in current_skills}
    required_set = {skill.lower() for skill in required}

    groups = {
        "Programming": ["Python", "Java", "JavaScript", "TypeScript"],
        "Data & SQL": ["SQL", "Pandas", "NumPy", "Data Analysis", "Excel"],
        "Machine Learning": ["Machine Learning", "Scikit-learn", "Deep Learning"],
        "Deployment": ["Docker", "AWS", "MLOps", "FastAPI"],
        "Visualization": ["Power BI", "Tableau", "Visualization"],
        "Collaboration": ["Git", "GitHub", "Communication"],
    }

    radar = []
    for axis, skills in groups.items():
        group_required = [s for s in skills if s.lower() in required_set] or skills[:2]
        matched = [s for s in group_required if s.lower() in current]
        radar.append({
            "axis": axis,
            "current": round((len(matched) / max(len(group_required), 1)) * 100),
            "required": 80 if any(s.lower() in required_set for s in skills) else 50,
        })
    return radar
