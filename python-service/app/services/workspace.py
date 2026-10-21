"""Owner-scoped saved opportunities and optimistic, versioned draft writes."""
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from firebase_admin import firestore

from app.models import Grant, StartupProfile
from app.services.firestore import get_firestore_client


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def opportunity_id(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [(key, value) for key, value in parse_qsl(parts.query) if not key.lower().startswith("utm_")]
    canonical = urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", urlencode(sorted(query)), ""))
    return hashlib.sha256(canonical.encode()).hexdigest()


def collection(uid: str, name: str):
    return get_firestore_client().collection("users").document(uid).collection(name)


def load_opportunity(uid: str, record_id: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{64}", record_id):
        raise LookupError("Opportunity not found.")
    snapshot = collection(uid, "opportunities").document(record_id).get()
    if not snapshot.exists:
        raise LookupError("Opportunity not found.")
    return snapshot.to_dict()


def save_opportunities(uid: str, grants: list[Grant]) -> None:
    batch = get_firestore_client().batch()
    for grant in grants:
        grant.id = opportunity_id(grant.source_url)
        grant.checked_at = grant.checked_at or now_iso()
        grant.source_version = fingerprint(grant.model_dump(include={"title", "application_url", "eligibility_criteria", "clean_markdown", "inspection"}))
        # Re-discovery replaces stale assessments but never rewrites a saved draft.
        batch.set(collection(uid, "opportunities").document(grant.id), grant.model_dump())
    if grants:
        batch.commit()


def save_assessment(uid: str, grant: Grant, assessment: dict, profile: StartupProfile) -> None:
    reference = collection(uid, "opportunities").document(grant.id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        snapshot = reference.get(transaction=transaction)
        if not snapshot.exists or snapshot.to_dict().get("source_version") != grant.source_version:
            raise ValueError("The opportunity changed during assessment. Refresh and assess again.")
        transaction.update(reference, {**assessment, "assessment_profile": fingerprint(profile.model_dump())})
    apply(transaction)


def list_workspace(uid: str) -> dict:
    opportunities = [doc.to_dict() for doc in collection(uid, "opportunities").order_by("checked_at", direction=firestore.Query.DESCENDING).limit(50).stream()]
    profile = get_firestore_client().collection("users").document(uid).get()
    profile_version = fingerprint(StartupProfile.model_validate(profile.to_dict()).model_dump()) if profile.exists else None
    for opportunity in opportunities:
        if opportunity.get("assessment_profile") != profile_version:
            opportunity.update(match_score=None, match_reason=None, eligibility_checks=[])
    drafts = [doc.to_dict() for doc in collection(uid, "drafts").order_by("updated_at", direction=firestore.Query.DESCENDING).limit(50).stream()]
    inspections = [doc.to_dict() for doc in collection(uid, "inspections").order_by("updated_at", direction=firestore.Query.DESCENDING).limit(50).stream()]
    return {"opportunities": opportunities, "drafts": drafts, "inspections": inspections}


def next_draft(current: dict | None, request: dict, grant: dict) -> dict:
    revision = (current or {}).get("revision", 0)
    if request["expected_revision"] != revision:
        raise ValueError("This draft was edited elsewhere. Reload before saving.")
    if request["source_version"] != grant.get("source_version"):
        raise ValueError("The opportunity changed. Refresh its requirements before saving.")
    return {"opportunity_id": grant["id"], "answers": request["answers"], "revision": revision + 1,
            "source_version": request["source_version"], "profile": request["profile"],
            "updated_at": now_iso()}


def save_draft(uid: str, record_id: str, request: dict) -> dict:
    load_opportunity(uid, record_id)
    reference = collection(uid, "drafts").document(record_id)
    grant_ref = collection(uid, "opportunities").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        grant = grant_ref.get(transaction=transaction)
        current = reference.get(transaction=transaction)
        if not grant.exists:
            raise LookupError("Opportunity not found.")
        draft = next_draft(current.to_dict() if current.exists else None, request, grant.to_dict())
        transaction.set(reference, draft)
        transaction.set(reference.collection("revisions").document(str(draft["revision"])), draft)
        return draft
    return apply(transaction)
