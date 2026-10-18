from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import DraftApplicationRequest, ExecuteApplicationRequest, ScoreGrantRequest, StartupProfile
from app.services.firestore import load_profile
from app.services.gemini import draft_answers, score_grant
from app.services.tinyfish import UpstreamServiceError, discover_and_parse_grants, execute_web_agent

app = FastAPI(title="AutoGrant AI Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins.split(","), allow_methods=["*"], allow_headers=["*"])


def profile_or_firestore(profile: StartupProfile | None, user_id: str | None) -> StartupProfile:
    if profile:
        return profile
    if not user_id:
        raise HTTPException(422, "Provide profile or user_id.")
    try:
        return load_profile(user_id)
    except (RuntimeError, LookupError) as error:
        raise HTTPException(404, str(error)) from error


@app.get("/health")
async def health(): return {"status": "ok"}


@app.post("/api/discover-grants")
async def discover_grants():
    try:
        return {"grants": [grant.model_dump() for grant in await discover_and_parse_grants()]}
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@app.post("/api/score-grant")
async def score(request: ScoreGrantRequest):
    try:
        value, reason = await score_grant(profile_or_firestore(request.profile, request.user_id), request.grant)
        return {"match_score": value, "match_reason": reason}
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@app.post("/api/draft-application")
async def draft(request: DraftApplicationRequest):
    try:
        return {"answers": await draft_answers(profile_or_firestore(request.profile, request.user_id), request.grant, request.questions)}
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@app.post("/api/execute-application")
async def execute(request: ExecuteApplicationRequest):
    if not request.confirm_submit:
        raise HTTPException(400, "Explicit confirm_submit=true is required before a submission run.")
    application_url = request.grant.application_url or request.grant.source_url
    try:
        return {"run": await execute_web_agent(application_url, request.drafted_answers, request.vault_credential_labels)}
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error
