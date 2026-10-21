from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.auth import authenticated_uid_for_execution
from app.services.inspection_runs import begin_inspection, refresh_inspection
from app.services.tinyfish import UpstreamServiceError
from app.services.workspace import load_opportunity

router = APIRouter(prefix="/api/workspace/inspections")


class InspectRequest(BaseModel):
    source_version: str = Field(pattern=r"^[a-f0-9]{64}$")


@router.post("/{record_id}")
async def inspect(record_id: str, request: InspectRequest, uid: str = Depends(authenticated_uid_for_execution)):
    try:
        return {"inspection": await begin_inspection(uid, record_id, request.source_version)}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error


@router.get("/{record_id}")
async def inspect_status(record_id: str, uid: str = Depends(authenticated_uid_for_execution)):
    try:
        record = await refresh_inspection(uid, record_id)
        return {"inspection": record, "grant": await run_in_threadpool(load_opportunity, uid, record_id)}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except UpstreamServiceError as error:
        raise HTTPException(error.status_code, str(error)) from error
