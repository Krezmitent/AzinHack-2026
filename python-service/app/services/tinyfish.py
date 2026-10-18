import asyncio
import ipaddress
import json
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.models import Grant

SEARCH_URL = "https://api.search.tinyfish.ai"
FETCH_URL = "https://api.fetch.tinyfish.ai"
AGENT_URL = "https://agent.tinyfish.ai/v1/automation/run-async"
RUNS_URL = "https://agent.tinyfish.ai/v1/runs"
DISCOVERY_TTL_SECONDS = 600
DISCOVERY_CACHE_MAX_LOCATIONS = 64
_discovery_lock = asyncio.Lock()
_discovery_cache: dict[tuple[str, str], tuple[float, list[Grant]]] = {}


class UpstreamServiceError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> dict[str, str]:
    if not settings.tinyfish_api_key:
        raise UpstreamServiceError("TINYFISH_API_KEY is not configured.", 503)
    return {"X-API-Key": settings.tinyfish_api_key, "Content-Type": "application/json"}


async def _request(method: str, url: str, *, retry: bool = True, timeout: float = 20.0, **kwargs: Any) -> httpx.Response:
    """Retry read-only calls; an Agent POST may already have started after a timeout."""
    headers = _headers()
    attempts = 2 if retry else 1
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for attempt in range(attempts):
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
            except httpx.RequestError as error:
                if attempt == attempts - 1:
                    raise UpstreamServiceError("TinyFish is unreachable or timed out. Check run status before retrying.") from error
                await asyncio.sleep(2 ** attempt)
                continue

            if response.status_code in (429, 500, 502, 503, 504):
                if attempt == attempts - 1:
                    status = 429 if response.status_code == 429 else 502
                    raise UpstreamServiceError("TinyFish is temporarily unavailable. Check run status before retrying.", status)
                await asyncio.sleep(2 ** attempt)
                continue
            if response.status_code in (401, 403):
                raise UpstreamServiceError("TinyFish rejected the configured API key.", 503)
            if response.status_code >= 400:
                raise UpstreamServiceError(f"TinyFish rejected the request (HTTP {response.status_code}).")
            return response
    raise UpstreamServiceError("TinyFish request exhausted retries.")


def _response_json(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as error:
        raise UpstreamServiceError("TinyFish returned invalid JSON.") from error
    if not isinstance(data, dict):
        raise UpstreamServiceError("TinyFish returned an unexpected JSON shape.")
    return data


def _web_url(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) > 2048:
        return None
    try:
        parsed = urlparse(value.strip())
        valid = parsed.scheme in ("http", "https") and parsed.hostname and not parsed.username and not parsed.password
    except ValueError:
        return None
    if not valid:
        return None
    return value.strip()


def _search_url(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if "://" not in candidate and "." in candidate.split("/", 1)[0]:
        candidate = "https://" + candidate
    return _web_url(candidate)


def _public_https_url(value: str) -> bool:
    if len(value) > 2048 or any(character.isspace() or ord(character) < 32 for character in value):
        return False
    url = _web_url(value)
    if not url:
        return False
    parsed = urlparse(url)
    host = (parsed.hostname or "").rstrip(".").lower()
    if parsed.scheme != "https" or host == "localhost" or host.endswith((".localhost", ".local", ".internal", ".test", ".invalid")):
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return "." in host
    return address.is_global


async def search_grants(location: str, sector: str) -> list[dict[str, Any]]:
    year = datetime.now(timezone.utc).year
    response = await _request("GET", SEARCH_URL, params={"query": f"{sector} startup grants open to founders in {location} {year}", "language": "en"})
    results = _response_json(response).get("results")
    if not isinstance(results, list):
        raise UpstreamServiceError("TinyFish Search returned an invalid result list.")
    valid_results = []
    for item in results:
        if isinstance(item, dict) and (url := _search_url(item.get("url"))):
            valid_results.append({**item, "url": url})
    return valid_results[:8]


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
            application_url = _web_url(urljoin(base_url, anchor["href"]))
            if application_url:
                break
    clean_markdown = ("# Grant details\n\n" + "\n\n".join(lines[:120]))[:100_000]
    return criteria, application_url, clean_markdown


async def discover_and_parse_grants(location: str, sector: str) -> list[Grant]:
    location = " ".join(location.split())
    sector = " ".join(sector.split())
    key = (location.casefold(), sector.casefold())
    cached = _discovery_cache.get(key)
    if cached is not None and time.monotonic() < cached[0]:
        return [grant.model_copy(deep=True) for grant in cached[1]]
    async with _discovery_lock:
        cached = _discovery_cache.get(key)
        if cached is not None and time.monotonic() < cached[0]:
            return [grant.model_copy(deep=True) for grant in cached[1]]
        grants = await _discover_uncached(location, sector)
        now = time.monotonic()
        for stale_key, (expiry, _) in list(_discovery_cache.items()):
            if expiry <= now:
                del _discovery_cache[stale_key]
        if len(_discovery_cache) >= DISCOVERY_CACHE_MAX_LOCATIONS:
            oldest_key = min(_discovery_cache, key=lambda cache_key: _discovery_cache[cache_key][0])
            del _discovery_cache[oldest_key]
        _discovery_cache[key] = (now + DISCOVERY_TTL_SECONDS, grants)
        return [grant.model_copy(deep=True) for grant in grants]


async def _discover_uncached(location: str, sector: str) -> list[Grant]:
    results = await search_grants(location, sector)
    urls = list(dict.fromkeys(item["url"] for item in results))
    if not urls:
        return []
    # Fetch supports clean Markdown, JSON, or HTML. HTML is selected here so links and
    # eligibility sections can be parsed deterministically into the Grant JSON model.
    response = await _request("POST", FETCH_URL, json={"urls": urls, "format": "html", "links": True})
    fetched = _response_json(response).get("results")
    if not isinstance(fetched, list):
        raise UpstreamServiceError("TinyFish Fetch returned an invalid result list.")
    fetched_by_url = {
        normalized: item
        for item in fetched
        if isinstance(item, dict) and (normalized := _search_url(item.get("url")))
    }
    grants: list[Grant] = []
    for result in {item["url"]: item for item in results}.values():
        url = result["url"]
        page = fetched_by_url.get(url, {})
        html = page.get("text") or page.get("content") or ""
        if not isinstance(html, str) or len(html.strip()) < 40:
            continue
        criteria, application_url, clean_markdown = _criteria_and_link(html[:250_000], url)
        page_title = page.get("title") or result.get("title")
        title = page_title.strip()[:300] if isinstance(page_title, str) and page_title.strip() else "Untitled grant"
        grants.append(Grant(title=title, source_url=url, application_url=application_url, eligibility_criteria=criteria, clean_markdown=clean_markdown))
    return grants


def validate_agent_request(application_url: str, credential_item_ids: list[str]) -> None:
    if not _public_https_url(application_url):
        raise UpstreamServiceError("The grant application URL must be a public HTTPS address.", 422)
    if credential_item_ids:
        # A single service API key has one Vault owner. Until Vault access is bound to
        # each verified AutoGrant user, allowing client-supplied IDs crosses tenants.
        raise UpstreamServiceError("Vault sign-in is not available for this account. Open the provider portal yourself if it requires login.", 422)


async def start_web_agent(application_url: str, answers: dict[str, str], credential_item_ids: list[str]) -> str:
    validate_agent_request(application_url, credential_item_ids)
    safe_answers = json.dumps(answers, ensure_ascii=False)
    payload = {
        "url": application_url,
        # TinyFish receives task instructions, not secrets. It discovers fields on the page.
        "goal": (
            "Open the grant application. Do not attempt to log in or create an account. If authentication is required, "
            "stop and return submitted false with a clear explanation. Find the application form, map each question to the corresponding drafted "
            f"answer from this JSON: {safe_answers}. Complete required non-sensitive fields from these answers, "
            "review that the form is complete, then click the final Submit/Send Application button only if no "
            "legal terms or attestations require applicant acceptance. Do not invent information or accept legal "
            "terms on the applicant's behalf. Return JSON with submitted (boolean), confirmation_number or "
            "confirmation_url only when the site shows one (copy it exactly; never invent it), and a concise explanation. Set submitted true only when "
            "the site confirms receipt; otherwise set it false."
        ),
        "use_vault": False,
        "output_schema": {
            "type": "object",
            "properties": {
                "submitted": {"type": "boolean"},
                "confirmation_number": {"type": "string"},
                "confirmation_url": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": ["submitted", "explanation"],
        },
    }
    # This POST starts a consequential run. Never retry: a timeout may mean the
    # first run started successfully, and a second request could submit twice.
    response = await _request("POST", AGENT_URL, json=payload, retry=False, timeout=30.0)
    data = _response_json(response)
    run_id = data.get("run_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", run_id) or data.get("error"):
        raise UpstreamServiceError("TinyFish did not return a valid run ID. Check the provider before trying again.")
    return run_id


async def get_web_agent_run(run_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", run_id):
        raise UpstreamServiceError("Invalid TinyFish run ID.", 422)
    response = await _request("GET", f"{RUNS_URL}/{run_id}", timeout=20.0)
    data = _response_json(response)
    if data.get("run_id") != run_id:
        raise UpstreamServiceError("TinyFish returned a mismatched run ID.")
    provider_status = data.get("status")
    if provider_status in ("PENDING", "RUNNING"):
        return {"status": "pending", "message": "The application run is in progress. This is not a submission confirmation.",
                "provider_status": provider_status, "run_id": run_id}
    result = data.get("result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except ValueError:
            pass
    if isinstance(result, dict):
        confirmation = result.get("confirmation_number") or result.get("confirmation_url")
        explanation = result.get("explanation")
        evidence = str(confirmation)[:500] if confirmation else ""
        if provider_status == "COMPLETED" and result.get("submitted") is True and evidence:
            return {"status": "submitted", "message": "The provider reported a completed run with submission confirmation.", "evidence": evidence, "provider_status": provider_status, "run_id": run_id}
        if provider_status == "COMPLETED" and result.get("submitted") is False:
            message = str(explanation).strip()[:500] if explanation else "The application was not submitted. Review the source form."
            return {"status": "not_submitted", "message": message, "evidence": evidence, "provider_status": provider_status, "run_id": run_id}

    return {
        "status": "unknown",
        "message": "Submission could not be verified. Check the grant portal before starting another run.",
        "evidence": "",
        "provider_status": provider_status if isinstance(provider_status, str) else None,
        "run_id": run_id,
    }
