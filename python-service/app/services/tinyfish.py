import asyncio
import json
import re
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models import Grant

SEARCH_URL = "https://api.search.tinyfish.ai"
FETCH_URL = "https://api.fetch.tinyfish.ai"
AGENT_URL = "https://agent.tinyfish.ai/v1/automation/run"


class UpstreamServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> dict[str, str]:
    if not settings.tinyfish_api_key:
        raise UpstreamServiceError("TINYFISH_API_KEY is not configured.", 503)
    return {"X-API-Key": settings.tinyfish_api_key, "Content-Type": "application/json"}


async def _request(method: str, url: str, **kwargs: Any) -> httpx.Response:
    """Retry transient TinyFish failures; 429s use a short exponential backoff."""
    async with httpx.AsyncClient(timeout=35.0, follow_redirects=True) as client:
        for attempt in range(3):
            try:
                response = await client.request(method, url, headers=_headers(), **kwargs)
                if response.status_code not in (429, 500, 502, 503, 504):
                    response.raise_for_status()
                    return response
                if attempt == 2:
                    raise UpstreamServiceError(f"TinyFish returned {response.status_code}: {response.text[:250]}", response.status_code)
                await asyncio.sleep(2 ** attempt)
            except httpx.HTTPError as error:
                if attempt == 2:
                    raise UpstreamServiceError(f"TinyFish request failed: {error}") from error
                await asyncio.sleep(2 ** attempt)
    raise UpstreamServiceError("TinyFish request exhausted retries.")


async def search_grants() -> list[dict[str, Any]]:
    response = await _request("GET", SEARCH_URL, params={"query": "startup funding grants 2026", "location": "US", "language": "en"})
    return response.json().get("results", [])[:8]


def _criteria_and_link(html: str, base_url: str) -> tuple[list[str], str | None, str]:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "nav", "footer", "header", "aside"]):
        node.decompose()
    text = re.sub(r"\n{3,}", "\n\n", soup.get_text("\n", strip=True))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    markers = ("eligib", "who can apply", "requirements", "qualified", "criteria")
    candidates = [line for line in lines if any(marker in line.lower() for marker in markers)]
    criteria = candidates[:8] or ["Review the source page for eligibility requirements."]
    application_url = None
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True).lower()
        if any(word in label for word in ("apply", "application", "submit proposal")):
            application_url = urljoin(base_url, anchor["href"])
            break
    clean_markdown = "# Grant details\n\n" + "\n\n".join(lines[:120])
    return criteria, application_url, clean_markdown


async def discover_and_parse_grants() -> list[Grant]:
    results = await search_grants()
    urls = [item.get("url") for item in results if item.get("url")]
    if not urls:
        return []
    # Fetch supports clean Markdown, JSON, or HTML. HTML is selected here so links and
    # eligibility sections can be parsed deterministically into the Grant JSON model.
    response = await _request("POST", FETCH_URL, json={"urls": urls, "format": "html", "links": True})
    fetched_by_url = {item.get("url"): item for item in response.json().get("results", [])}
    grants: list[Grant] = []
    for result in results:
        url = result["url"]
        fetched = fetched_by_url.get(url, {})
        html = fetched.get("text") or fetched.get("content") or ""
        if not html:
            continue
        criteria, application_url, clean_markdown = _criteria_and_link(html, url)
        grants.append(Grant(title=fetched.get("title") or result.get("title") or "Untitled grant", source_url=url, application_url=application_url, eligibility_criteria=criteria, clean_markdown=clean_markdown))
    return grants


async def execute_web_agent(application_url: str, answers: dict[str, str], credential_labels: list[str]) -> Any:
    safe_answers = json.dumps(answers, ensure_ascii=False)
    payload = {
        "url": application_url,
        # TinyFish receives task instructions, not secrets. It discovers fields on the page
        # and maps answer labels/text; its browser runtime resolves only approved Vault labels.
        "goal": (
            "Open the grant application. Authenticate only if required using the approved TinyFish Vault "
            "credential(s). Find the application form, map each question to the corresponding drafted "
            f"answer from this JSON: {safe_answers}. Complete required non-sensitive fields from these answers, "
            "review that the form is complete, then click the final Submit/Send Application button. "
            "Do not invent information or accept legal terms on the applicant's behalf. Return a concise status."
        ),
        # Per TinyFish Vault, these are pre-approved label references—not usernames, passwords, or MFA codes.
        "credentials": credential_labels,
        "use_vault": bool(credential_labels),
    }
    response = await _request("POST", AGENT_URL, json=payload)
    try:
        return response.json()
    except ValueError:
        return {"raw": response.text[:3000]}
