from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from app.auth import authenticated_uid, authenticated_uid_for_execution
from app.config import settings
from app.models import DiscoverGrantsRequest, DraftApplicationRequest, ExecuteApplicationRequest, Grant, ScoreGrantRequest, StartupProfile
from app.services.firestore import (grant_was_discovered, load_profile, load_application_run,
                                    list_application_runs, record_discovered_grants,
                                    reserve_application_run, update_application_run)
from app.services.gemini import draft_answers, assess_grant
from app.services.workspace import load_opportunity, save_assessment
from app.workspace_routes import router as workspace_router
from app.inspection_routes import router as inspection_router
from app.services.inspection import draft_questions
from app.services.inspection_runs import reviewed_grant
from app.services.tinyfish import (UpstreamServiceError, discover_and_parse_grants, get_web_agent_run,
                                   start_web_agent, validate_agent_request)

app = FastAPI(title="AutoGrant AI Service", version="1.0.0")
app.include_router(workspace_router)
app.include_router(inspection_router)
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins.split(","), allow_methods=["*"], allow_headers=["*"])


def profile_or_firestore(profile: StartupProfile | None, user_id: str | None, uid: str) -> StartupProfile:
    if user_id is not None and user_id != uid:
        raise HTTPException(403, "You cannot access another user's profile.")
    if profile:
        return profile
    try:
        return load_profile(uid)
    except (RuntimeError, LookupError) as error:
        raise HTTPException(404, str(error)) from error


@app.get("/health")
async def health(): return {"status": "ok"}


@app.get("/ready")
async def ready():
    configured = {
        "firebase": bool(settings.firebase_service_account_json),
        "tinyfish": bool(settings.tinyfish_api_key),
        "gemini": bool(settings.gemini_api_key),
    }
    return {"ready": all(configured.values()), "configured": configured}


@app.post("/api/discover-grants")
async def discover_grants(request: DiscoverGrantsRequest, uid: str = Depends(authenticated_uid)):
    try:
        grants = await discover_and_parse_grants(request.location, request.sector)
        await run_in_threadpool(record_discovered_grants, uid, grants)
        return {"grants": [grant.model_dump() for grant in grants]}
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@app.post("/api/score-grant")
async def score(request: ScoreGrantRequest, uid: str = Depends(authenticated_uid)):
    try:
        saved = await run_in_threadpool(load_opportunity, uid, request.grant.id or "")
        grant = Grant.model_validate(saved)
        profile = profile_or_firestore(request.profile, request.user_id, uid)
        assessment = await assess_grant(profile, grant)
        await run_in_threadpool(save_assessment, uid, grant, assessment.model_dump(), profile)
        return assessment.model_dump()
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@app.post("/api/draft-application")
async def draft(request: DraftApplicationRequest, uid: str = Depends(authenticated_uid)):
    try:
        grant = Grant.model_validate(await run_in_threadpool(load_opportunity, uid, request.grant.id or ""))
        if request.grant.source_version != grant.source_version:
            raise ValueError("The source changed. Reload before drafting.")
        questions = draft_questions(grant)
        if not questions or request.questions != questions:
            raise ValueError("Draft questions must match the latest inspected form.")
        return {"answers": await draft_answers(profile_or_firestore(request.profile, request.user_id, uid), grant, questions)}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@app.post("/api/execute-application")
async def execute(request: ExecuteApplicationRequest, uid: str = Depends(authenticated_uid_for_execution)):
    if not request.confirm_submit:
        raise HTTPException(400, "Explicit confirm_submit=true is required before a submission run.")
    application_url = request.grant.application_url or request.grant.source_url
    try:
        validate_agent_request(application_url, request.vault_credential_labels)
        if not settings.tinyfish_api_key:
            raise HTTPException(503, "TinyFish is not configured. No application run was started.")
        if not await run_in_threadpool(grant_was_discovered, uid, request.grant):
            raise HTTPException(403, "This grant was not discovered for your account recently. Scan for grants again.")
        request.grant = await run_in_threadpool(reviewed_grant, uid, request)
        application_url = request.grant.application_url or request.grant.source_url
        validate_agent_request(application_url, request.vault_credential_labels)
        # The reservation is committed before the consequential provider POST. Repeat clicks
        # and retries return the same record, including when the first response was lost.
        run, created = await run_in_threadpool(reserve_application_run, uid, request.grant)
        if not created:
            return {"run": run}
        try:
            run_id = await start_web_agent(application_url, request.drafted_answers, request.vault_credential_labels)
        except UpstreamServiceError as error:
            # Even a timeout can mean the provider accepted the POST. Never dispatch again.
            return {"run": await run_in_threadpool(update_application_run, uid, run["id"], {
                "status": "unknown",
                "message": f"Could not verify whether the run started: {error}. Check the grant portal and contact support before another attempt.",
            })}
        return {"run": await run_in_threadpool(update_application_run, uid, run["id"], {
            "status": "pending", "run_id": run_id, "provider_status": "PENDING",
            "message": "The application run started. Submission is not confirmed.",
        })}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@app.get("/api/application-runs")
async def application_runs(uid: str = Depends(authenticated_uid_for_execution)):
    return {"runs": await run_in_threadpool(list_application_runs, uid)}


@app.get("/api/application-runs/{record_id}")
async def application_run(record_id: str, uid: str = Depends(authenticated_uid_for_execution)):
    if len(record_id) != 64 or any(character not in "0123456789abcdef" for character in record_id):
        raise HTTPException(422, "Invalid application run ID.")
    try:
        run = await run_in_threadpool(load_application_run, uid, record_id)
    except LookupError as error:
        raise HTTPException(404, str(error)) from error

    if run["status"] in ("submitted", "not_submitted", "unknown"):
        return {"run": run}
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(run["created_at"])).total_seconds()
    if run["status"] == "starting":
        if age > 90:
            run = await run_in_threadpool(update_application_run, uid, record_id, {
                "status": "unknown", "message": "The start request ended without a run ID. Check the grant portal before trying again.",
            })
        return {"run": run}
    if age > 86_400:
        run = await run_in_threadpool(update_application_run, uid, record_id, {
            "status": "unknown", "message": "Run status was not confirmed within 24 hours. Check the grant portal.",
        })
        return {"run": run}
    if not run.get("run_id"):
        return {"run": run}
    try:
        status = await get_web_agent_run(run["run_id"])
    except UpstreamServiceError:
        # Transient status failures do not prove anything about the provider run.
        return {"run": {**run, "message": "Run status is temporarily unavailable. Keep checking; submission is not confirmed."}}
    return {"run": await run_in_threadpool(update_application_run, uid, record_id, status)}
