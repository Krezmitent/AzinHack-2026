from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from starlette.concurrency import run_in_threadpool

from app.auth import authenticated_uid
from app.models import StartupProfile
from app.services.workspace import list_workspace, save_draft

router = APIRouter(prefix="/api/workspace")


class SaveDraftRequest(BaseModel):
    answers: dict[str, str] = Field(min_length=1, max_length=20)
    profile: StartupProfile
    source_version: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_revision: int = Field(ge=0)

    @field_validator("answers")
    @classmethod
    def valid_answers(cls, value):
        if any(not question.strip() or len(question) > 500 or len(answer) > 10000 for question, answer in value.items()) or not any(answer.strip() for answer in value.values()):
            raise ValueError("Save at least one answer and keep all questions and answers within their size limits.")
        return value


@router.get("")
async def workspace(uid: str = Depends(authenticated_uid)):
    return await run_in_threadpool(list_workspace, uid)


@router.post("/drafts/{record_id}")
async def store_draft(record_id: str, request: SaveDraftRequest, uid: str = Depends(authenticated_uid)):
    try:
        return {"draft": await run_in_threadpool(save_draft, uid, record_id, request.model_dump())}
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(409, str(error)) from error
