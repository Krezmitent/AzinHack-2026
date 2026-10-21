import json

from fastapi import APIRouter, Depends, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from app.auth import authenticated_uid, authenticated_uid_for_execution
from app.monitor_models import ApplicationUpdate, WatchAction, WatchRequest
from app.services.applications import update_application
from app.services.monitors import authenticate_callback, enqueue_run, public_watch, reserve_watch, watch_action
from app.services.tinyfish import UpstreamServiceError
from app.services.workspace import collection, load_opportunity

router = APIRouter(prefix="/api/workspace")
webhooks = APIRouter(prefix="/webhooks/tinyfish")


def radar_data(uid: str) -> dict:
    watches = [public_watch(snapshot.to_dict()) for snapshot in collection(uid, "watches").order_by("created_at").limit(50).stream() if snapshot.to_dict()["status"] != "deleted"]
    events = [snapshot.to_dict() for snapshot in collection(uid, "events").order_by("created_at", direction="DESCENDING").limit(50).stream()]
    applications = [snapshot.to_dict() for snapshot in collection(uid, "applications").order_by("updated_at", direction="DESCENDING").limit(50).stream()]
    return {"watches": watches, "events": events, "applications": applications}


@router.get("/radar")
async def radar(uid: str = Depends(authenticated_uid)):
    return await run_in_threadpool(radar_data, uid)


@router.get("/opportunities/{record_id}")
async def saved_opportunity(record_id: str, uid: str = Depends(authenticated_uid)):
    try:
        return {"grant": await run_in_threadpool(load_opportunity, uid, record_id)}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error


@router.post("/watches")
async def create_watch(request: WatchRequest, uid: str = Depends(authenticated_uid_for_execution)):
    try:
        return {"watch": public_watch(await run_in_threadpool(reserve_watch, uid, request))}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@router.post("/watches/{record_id}")
async def control_watch(record_id: str, request: WatchAction, uid: str = Depends(authenticated_uid_for_execution)):
    try:
        return {"watch": public_watch(await watch_action(uid, record_id, request.action))}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@router.post("/applications/{record_id}")
async def application_status(record_id: str, request: ApplicationUpdate, uid: str = Depends(authenticated_uid_for_execution)):
    try:
        return {"application": await run_in_threadpool(update_application, uid, record_id, request.model_dump())}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error


@router.post("/events/{record_id}/read")
async def read_event(record_id: str, uid: str = Depends(authenticated_uid)):
    import re
    if not re.fullmatch(r"[a-f0-9]{64}", record_id):
        raise HTTPException(404, "Update not found.")
    reference = collection(uid, "events").document(record_id)
    snapshot = await run_in_threadpool(reference.get)
    if not snapshot.exists:
        raise HTTPException(404, "Update not found.")
    await run_in_threadpool(reference.update, {"read": True})
    return {"read": True}


@webhooks.post("/monitor/{callback_id}/{secret}")
async def monitor_callback(callback_id: str, secret: str, request: Request):
    try:
        callback = await run_in_threadpool(authenticate_callback, callback_id, secret)
    except (PermissionError, LookupError) as error:
        raise HTTPException(403, "Invalid callback.") from error
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 512 * 1024:
            raise HTTPException(413, "Monitor payload exceeds the size limit.")
    try:
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Invalid callback payload.")
        key = await run_in_threadpool(enqueue_run, callback["uid"], callback["watch_id"], payload)
        return {"accepted": True, "id": key}
    except (ValueError, UnicodeDecodeError) as error:
        raise HTTPException(400, "Invalid callback payload.") from error
