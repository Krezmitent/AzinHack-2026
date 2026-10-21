"""Durable inspection reservations shared by dashboard polling and the worker."""
from datetime import datetime, timezone
from uuid import uuid4

from firebase_admin import firestore
from starlette.concurrency import run_in_threadpool

from app.models import Grant
from app.services import inspection
from app.services.firestore import _run_id, get_firestore_client
from app.services.workspace import collection, fingerprint, load_opportunity, now_iso

ACTIVE = ("starting", "pending")


def work_reference(uid: str, record_id: str):
    return get_firestore_client().collection("work_items").document(fingerprint({"uid": uid, "id": record_id, "kind": "inspection"}))


def load_inspection(uid: str, record_id: str) -> dict:
    load_opportunity(uid, record_id)
    snapshot = collection(uid, "inspections").document(record_id).get()
    return snapshot.to_dict() if snapshot.exists else {"id": record_id, "status": "not_started"}


def reserve_inspection(uid: str, record_id: str, source_version: str) -> tuple[dict, bool]:
    load_opportunity(uid, record_id)
    reference = collection(uid, "inspections").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        grant = collection(uid, "opportunities").document(record_id).get(transaction=transaction).to_dict()
        previous = reference.get(transaction=transaction)
        if grant["source_version"] != source_version:
            raise ValueError("The opportunity changed. Reload before inspecting.")
        if previous.exists and previous.to_dict()["status"] in ACTIVE:
            return previous.to_dict(), False
        record = {"id": record_id, "generation": uuid4().hex, "status": "starting", "source_version": source_version,
                  "run_id": None, "streaming_url": None, "message": "Starting a read-only inspection.",
                  "created_at": now_iso(), "updated_at": now_iso()}
        transaction.set(reference, record)
        transaction.set(work_reference(uid, record_id), {"kind": "inspection", "uid": uid, "id": record_id, "status": "pending"})
        return record, True
    return apply(transaction)


def update_inspection(uid: str, record_id: str, generation: str, changes: dict, result=None) -> dict:
    reference = collection(uid, "inspections").document(record_id)
    grant_ref = collection(uid, "opportunities").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        current = reference.get(transaction=transaction).to_dict()
        grant = grant_ref.get(transaction=transaction).to_dict()
        if current["generation"] != generation or current["status"] not in ACTIVE:
            return current
        updates = {**changes, "updated_at": now_iso()}
        if result is not None:
            if grant["source_version"] != current["source_version"]:
                updates.update(status="stale", message="The source changed during inspection. Inspect the latest version again.")
            else:
                enriched = Grant.model_validate(grant).model_copy(update={
                    "inspection": result, "application_url": result.application_url or grant.get("application_url"),
                    "eligibility_criteria": result.eligibility_criteria or grant.get("eligibility_criteria", []),
                    "match_score": None, "match_reason": None, "eligibility_checks": [], "checked_at": now_iso()})
                value = enriched.model_dump()
                value["source_version"] = fingerprint({key: value[key] for key in ("title", "application_url", "eligibility_criteria", "clean_markdown", "inspection")})
                transaction.set(grant_ref, value)
                provenance = collection(uid, "discovered_grants").document(_run_id(enriched))
                transaction.set(provenance, {"source_url": enriched.source_url,
                                           "application_url": enriched.application_url or enriched.source_url, "discovered_at": now_iso()})
        record = {**current, **updates}
        transaction.update(reference, updates)
        transaction.set(reference.collection("attempts").document(generation), record)
        if record["status"] not in ACTIVE:
            transaction.set(work_reference(uid, record_id), {"kind": "inspection", "uid": uid, "id": record_id, "status": "complete"})
        return record
    return apply(transaction)


async def begin_inspection(uid: str, record_id: str, source_version: str) -> dict:
    grant = Grant.model_validate(await run_in_threadpool(load_opportunity, uid, record_id))
    inspection.validate_agent_request(grant.source_url, [])
    record, created = await run_in_threadpool(reserve_inspection, uid, record_id, source_version)
    if not created:
        return record
    try:
        run_id = await inspection.start_inspection(grant)
    except inspection.UpstreamServiceError:
        return await run_in_threadpool(update_inspection, uid, record_id, record["generation"], {
            "status": "unknown", "message": "Could not confirm the inspection start. A provider run may still exist; another inspection may incur an extra charge."})
    return await run_in_threadpool(update_inspection, uid, record_id, record["generation"], {
        "status": "pending", "run_id": run_id, "message": "TinyFish is inspecting the programme and application form."})


async def refresh_inspection(uid: str, record_id: str) -> dict:
    record = await run_in_threadpool(load_inspection, uid, record_id)
    if record["status"] not in ACTIVE:
        return record
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(record["created_at"])).total_seconds()
    changes = None
    if (record["status"] == "starting" and age > 90) or age > 900:
        changes = {"status": "unknown", "message": "Inspection could not be reconciled in time. Inspect again or use the provider portal."}
    elif record.get("run_id"):
        data = await inspection.fetch_inspection(record["run_id"])
        status = data.get("status")
        if status in ("PENDING", "QUEUED", "RUNNING"):
            changes = {"streaming_url": inspection.preview_url(data.get("streaming_url")), "message": "Inspecting the provider’s form. No data is being entered or submitted."}
        elif status == "COMPLETED":
            try:
                result = inspection.parse_inspection(data.get("result"))
            except inspection.UpstreamServiceError as error:
                changes = {"status": "failed", "message": str(error), "streaming_url": None}
            else:
                return await run_in_threadpool(update_inspection, uid, record_id, record["generation"],
                                              {"status": "completed", "message": result.explanation, "streaming_url": None}, result)
        else:
            changes = {"status": "failed", "message": "TinyFish could not complete the inspection. Review the provider portal.", "streaming_url": None}
    return await run_in_threadpool(update_inspection, uid, record_id, record["generation"], changes) if changes else record


def reviewed_grant(uid: str, request) -> Grant:
    grant = Grant.model_validate(load_opportunity(uid, request.grant.id or ""))
    active = load_inspection(uid, grant.id)
    if active["status"] in ACTIVE:
        raise ValueError("Wait for the current inspection before submitting.")
    saved = collection(uid, "drafts").document(grant.id).get()
    draft = saved.to_dict() if saved.exists else {}
    saved_answers = {key: value for key, value in draft.get("answers", {}).items() if value.strip() and not value.startswith("Information not provided;")}
    if (not request.draft_revision or request.draft_revision != draft.get("revision")
            or draft.get("source_version") != grant.source_version or saved_answers != request.drafted_answers):
        raise ValueError("Save and review the latest draft before starting an application run.")
    inspection.validate_form_answers(grant, request.drafted_answers)
    return grant
