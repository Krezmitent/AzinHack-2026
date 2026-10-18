import asyncio
import json
import re

import httpx

from app.config import settings
from app.models import Grant, StartupProfile
from app.services.tinyfish import UpstreamServiceError


def _api_url() -> str:
    if not settings.gemini_api_key:
        raise UpstreamServiceError("GEMINI_API_KEY is not configured.", 503)
    return f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"


async def _generate(prompt: str) -> str:
    async with httpx.AsyncClient(timeout=45.0) as client:
        for attempt in range(3):
            try:
                response = await client.post(_api_url(), json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.35, "responseMimeType": "application/json"}})
                if response.status_code == 429:
                    if attempt == 2:
                        raise UpstreamServiceError("Gemini is rate-limiting requests. Please retry shortly.", 429)
                    await asyncio.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                return response.json()["candidates"][0]["content"]["parts"][0]["text"]
            except (httpx.HTTPError, KeyError, IndexError) as error:
                if attempt == 2:
                    raise UpstreamServiceError(f"Gemini generation failed: {error}") from error
                await asyncio.sleep(2 ** attempt)
    raise UpstreamServiceError("Gemini generation exhausted retries.")


def _json(text: str) -> dict:
    return json.loads(re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip())


async def score_grant(profile: StartupProfile, grant: Grant) -> tuple[int, str]:
    prompt = f"""You score startup grant eligibility. Use only the supplied context. Return JSON {{\"score\": integer 0-100, \"reason\": string <= 35 words}}.
PROFILE: {profile.model_dump_json()}
GRANT: {grant.model_dump_json(include={{'title','eligibility_criteria','clean_markdown'}})}"""
    result = _json(await _generate(prompt))
    return max(0, min(100, int(result.get("score", 0)))), str(result.get("reason", "No explanation returned."))


async def draft_answers(profile: StartupProfile, grant: Grant, questions: list[str]) -> dict[str, str]:
    prompt = f"""Draft accurate, professional grant answers. Never fabricate metrics, certifications, ownership, or eligibility. Return JSON {{\"answers\": {{question: answer}}}} and answer every exact question.
STARTUP PROFILE: {profile.model_dump_json()}
GRANT: {grant.model_dump_json(include={{'title','eligibility_criteria'}})}
QUESTIONS: {json.dumps(questions)}"""
    result = _json(await _generate(prompt))
    answers = result.get("answers", {})
    return {question: str(answers.get(question, "Information not provided; please complete this response.")) for question in questions}
