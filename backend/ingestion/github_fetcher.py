"""
GitHub Fetcher
──────────────
Given a github.com URL, we pull three things via the GitHub REST API:
  1. Repository metadata (name, description, topics, stars)
  2. README content (decoded from base64)
  3. Language breakdown (e.g. {"Python": 8432, "JavaScript": 1200})

All three are stitched into one text blob so the chunker treats
the repo as a single rich document.

No auth token required for public repos (60 req/hr limit).
Set GITHUB_TOKEN in .env for 5000 req/hr.
"""

import re
import base64
import httpx
from fastapi import HTTPException
from backend.config import get_settings


GITHUB_API = "https://api.github.com"


def _parse_repo_path(url: str) -> tuple[str, str]:
    """Extract owner and repo name from a github.com URL."""
    # Handles: https://github.com/owner/repo
    #          https://github.com/owner/repo/tree/main/subdir
    match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
    if not match:
        raise HTTPException(400, f"Cannot parse GitHub repo from URL: {url}")
    return match.group(1), match.group(2).rstrip("/")


async def extract_github(url: str) -> dict:
    owner, repo = _parse_repo_path(url)

    headers = {"Accept": "application/vnd.github+json"}
    settings = get_settings()

    # Attach token if available
    token = getattr(settings, "github_token", None)
    if token and token != "placeholder":
        headers["Authorization"] = f"Bearer {token}"

    async with httpx.AsyncClient(timeout=15) as client:

        # 1. Repo metadata
        meta_resp = await client.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=headers)
        if meta_resp.status_code == 404:
            raise HTTPException(404, f"GitHub repo not found: {owner}/{repo}")
        meta = meta_resp.json()

        # 2. README
        readme_text = ""
        readme_resp = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/readme", headers=headers
        )
        if readme_resp.status_code == 200:
            content_b64 = readme_resp.json().get("content", "")
            readme_text = base64.b64decode(content_b64).decode("utf-8", errors="replace")

        # 3. Language stats
        lang_resp  = await client.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/languages", headers=headers
        )
        languages  = lang_resp.json() if lang_resp.status_code == 200 else {}

    # ── Assemble text blob ─────────────────────────────────────────────────
    lang_str = ", ".join(languages.keys()) if languages else "Not specified"
    topics   = ", ".join(meta.get("topics", [])) or "None"

    text_blob = f"""
GitHub Repository: {meta.get('full_name', f'{owner}/{repo}')}
Description: {meta.get('description') or 'No description'}
Topics/Tags: {topics}
Primary Languages: {lang_str}
Stars: {meta.get('stargazers_count', 0)} | Forks: {meta.get('forks_count', 0)}
Created: {meta.get('created_at', '')[:10]} | Last Updated: {meta.get('updated_at', '')[:10]}

--- README ---
{readme_text[:4000]}
""".strip()

    return {
        "text"      : text_blob,
        "extra_meta": {
            "owner"     : owner,
            "repo"      : repo,
            "stars"     : meta.get("stargazers_count", 0),
            "languages" : languages,
            "topics"    : meta.get("topics", []),
        },
    }
