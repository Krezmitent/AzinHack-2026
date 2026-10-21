from functools import lru_cache
from datetime import datetime, timezone
import hashlib

from firebase_admin import firestore
from google.api_core.exceptions import Conflict

from app.auth import get_admin_app
from app.models import Grant, StartupProfile


@lru_cache
def get_firestore_client():
    """Initialise only when server-side Firestore access is requested."""
    return firestore.client(app=get_admin_app())


def load_profile(user_id: str) -> StartupProfile:
    snapshot = get_firestore_client().collection("users").document(user_id).get()
    if not snapshot.exists:
        raise LookupError("No Firestore profile exists for this user.")
    return StartupProfile.model_validate(snapshot.to_dict())


def _run_collection(user_id: str):
    return get_firestore_client().collection("users").document(user_id).collection("application_runs")


def _run_id(grant: Grant) -> str:
    # One reservation per grant/application target and user, independent of answer edits.
    target = (grant.application_url or grant.source_url).strip()
    return hashlib.sha256(f"{grant.source_url.strip()}\n{target}".encode()).hexdigest()


def record_discovered_grants(user_id: str, grants: list[Grant]) -> None:
    from app.services.workspace import save_opportunities
    save_opportunities(user_id, grants)
    client = get_firestore_client()
    batch = client.batch()
    collection = client.collection("users").document(user_id).collection("discovered_grants")
    now = datetime.now(timezone.utc).isoformat()
    for grant in grants:
        batch.set(collection.document(_run_id(grant)), {
            "source_url": grant.source_url,
            "application_url": grant.application_url or grant.source_url,
            "discovered_at": now,
        })
    if grants:
        batch.commit()


def grant_was_discovered(user_id: str, grant: Grant) -> bool:
    snapshot = (get_firestore_client().collection("users").document(user_id)
                .collection("discovered_grants").document(_run_id(grant)).get())
    if not snapshot.exists:
        return False
    data = snapshot.to_dict()
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(data["discovered_at"])).total_seconds()
    return age < 7 * 86_400 and data.get("source_url") == grant.source_url and data.get("application_url") == (grant.application_url or grant.source_url)


def reserve_application_run(user_id: str, grant: Grant) -> tuple[dict, bool]:
    from app.services.work_queue import enqueue
    record_id = _run_id(grant)
    reference = _run_collection(user_id).document(record_id)
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "id": record_id, "grant_title": grant.title, "source_url": grant.source_url,
        "application_url": grant.application_url or grant.source_url,
        "status": "starting", "message": "Preparing the application run. No submission is confirmed.",
        "provider_status": None, "run_id": None, "evidence": None,
        "created_at": now, "updated_at": now,
        "opportunity_id": grant.id,
    }
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def reserve(transaction):
        snapshot = reference.get(transaction=transaction)
        if snapshot.exists:
            current = snapshot.to_dict()
            if current["status"] in ("starting", "pending"):
                enqueue(transaction, user_id, record_id, "application_run")
            return current, False
        transaction.set(reference, record)
        enqueue(transaction, user_id, record_id, "application_run")
        return record, True
    return reserve(transaction)


def update_application_run(user_id: str, record_id: str, changes: dict) -> dict:
    reference = _run_collection(user_id).document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        snapshot = reference.get(transaction=transaction)
        if not snapshot.exists:
            raise LookupError("Application run was not found.")
        current = snapshot.to_dict()
        if current["status"] in ("submitted", "not_submitted", "unknown"):
            return current
        updates = {**changes, "updated_at": datetime.now(timezone.utc).isoformat()}
        transaction.update(reference, updates)
        return {**current, **updates}

    return apply(transaction)


def load_application_run(user_id: str, record_id: str) -> dict:
    snapshot = _run_collection(user_id).document(record_id).get()
    if not snapshot.exists:
        raise LookupError("Application run was not found.")
    return snapshot.to_dict()


def list_application_runs(user_id: str) -> list[dict]:
    query = _run_collection(user_id).order_by("created_at", direction=firestore.Query.DESCENDING).limit(20)
    return [snapshot.to_dict() for snapshot in query.stream()]
