from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from starlette.concurrency import run_in_threadpool

from app.auth import authenticated_uid
from app.models import StartupProfile
from app.services.firestore import get_firestore_client

router = APIRouter(prefix="/api/profile")


def read_profile(uid: str) -> dict | None:
    snapshot = get_firestore_client().collection("users").document(uid).get()
    if not snapshot.exists:
        return None
    return snapshot.to_dict()


def write_profile(uid: str, profile: StartupProfile) -> dict:
    value = {**profile.model_dump(), "updatedAt": datetime.now(timezone.utc).isoformat()}
    get_firestore_client().collection("users").document(uid).set(value)
    return value


@router.get("")
async def get_profile(uid: str = Depends(authenticated_uid)):
    return {"profile": await run_in_threadpool(read_profile, uid)}


@router.post("")
async def put_profile(profile: StartupProfile, uid: str = Depends(authenticated_uid)):
    return {"profile": await run_in_threadpool(write_profile, uid, profile)}
