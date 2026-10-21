"""Application decisions stay separate from browser execution outcomes."""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from firebase_admin import firestore
from google.api_core.exceptions import Conflict
from google.cloud.firestore_v1.base_query import FieldFilter

from app.services.firestore import get_firestore_client
from app.services.workspace import collection, fingerprint, load_opportunity, now_iso, opportunity_id

CLOSED = ("awarded", "rejected", "withdrawn")


def event_record(kind: str, title: str, message: str, **details) -> dict:
    return {"kind": kind, "title": title, "message": message, "created_at": now_iso(), "read": False, **details}


def emit_event(uid: str, key: str, record: dict) -> None:
    try:
        collection(uid, "events").document(key).create({"id": key, **record})
    except Conflict:
        pass


def deadline_fields(grant: dict) -> dict:
    result = grant.get("inspection") or {}
    return {"deadline_date": result.get("deadline_date", "") if result.get("complete") else "",
            "deadline_source_version": grant.get("source_version", "")}


def schedule_reminder(transaction, uid: str, application: dict) -> None:
    deadline = application.get("deadline_date")
    if not deadline or application["status"] in CLOSED or application.get("reminder_sent_for") == deadline:
        return
    due = datetime.combine(date.fromisoformat(deadline) - timedelta(days=3), time(9), ZoneInfo(application["timezone"])).astimezone(timezone.utc)
    key = fingerprint({"uid": uid, "id": application["id"], "deadline": deadline})
    transaction.set(get_firestore_client().collection("reminders").document(key), {
        "uid": uid, "application_id": application["id"], "deadline_date": deadline, "due_at": due.isoformat()})


def update_application(uid: str, record_id: str, request: dict) -> dict:
    grant = load_opportunity(uid, record_id)
    reference = collection(uid, "applications").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        snapshot = reference.get(transaction=transaction)
        current = snapshot.to_dict() if snapshot.exists else {}
        if current.get("revision", 0) != request["expected_revision"]:
            raise ValueError("This application changed elsewhere. Reload its status before saving.")
        record = {**current, "id": record_id, "opportunity_id": record_id, "grant_title": grant["title"],
                  "application_url": grant.get("application_url") or grant["source_url"], "source_url": grant["source_url"],
                  "status": request["status"], "status_source": "founder_reported", "note": request["note"],
                  "timezone": request["timezone"], "revision": current.get("revision", 0) + 1,
                  "updated_at": now_iso(), "deadline_needs_review": False, **deadline_fields(grant)}
        transaction.set(reference, record)
        transaction.set(reference.collection("history").document(str(record["revision"])), record)
        schedule_reminder(transaction, uid, record)
        return record
    return apply(transaction)


def record_submission(uid: str, run: dict) -> None:
    if run["status"] != "submitted":
        return
    record_id = run.get("opportunity_id") or opportunity_id(run["source_url"])
    reference = collection(uid, "applications").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        snapshot = reference.get(transaction=transaction)
        grant_snapshot = collection(uid, "opportunities").document(record_id).get(transaction=transaction)
        current = snapshot.to_dict() if snapshot.exists else {}
        # A repeated receipt must never regress a later founder-reported decision.
        if current.get("status") not in (None, "draft"):
            return
        record = {**current, "id": record_id, "opportunity_id": record_id, "grant_title": run["grant_title"],
                  "application_url": run["application_url"], "source_url": run["source_url"], "status": "submitted",
                  "status_source": "submission_confirmation", "note": run.get("evidence", ""),
                  "timezone": current.get("timezone", "UTC"), "revision": current.get("revision", 0) + 1,
                  "updated_at": now_iso(), **deadline_fields(grant_snapshot.to_dict() if grant_snapshot.exists else {})}
        transaction.set(reference, record)
        transaction.set(reference.collection("history").document(str(record["revision"])), record)
        schedule_reminder(transaction, uid, record)
    apply(transaction)


def due_reminders() -> list:
    return list(get_firestore_client().collection("reminders").where(filter=FieldFilter("due_at", "<=", now_iso())).limit(50).stream())


def deliver_reminder(snapshot) -> None:
    item = snapshot.to_dict()
    reference = collection(item["uid"], "applications").document(item["application_id"])
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        reminder = snapshot.reference.get(transaction=transaction)
        current = reference.get(transaction=transaction)
        grant = collection(item["uid"], "opportunities").document(item["application_id"]).get(transaction=transaction)
        if not reminder.exists:
            return
        application = current.to_dict() if current.exists else {}
        if (application.get("deadline_date") == item["deadline_date"] and application.get("status") not in CLOSED
                and application.get("reminder_sent_for") != item["deadline_date"] and grant.exists
                and application.get("deadline_source_version") == grant.to_dict().get("source_version")):
            key = fingerprint({"application": item["application_id"], "deadline": item["deadline_date"]})
            transaction.set(collection(item["uid"], "events").document(key), {"id": key, **event_record(
                "deadline_reminder", application["grant_title"], f"Provider deadline date: {item['deadline_date']}. Verify the exact cutoff time at the source.",
                opportunity_id=item["application_id"], source_url=application["source_url"], requires_review=True)})
            transaction.update(reference, {"reminder_sent_for": item["deadline_date"]})
        transaction.delete(snapshot.reference)
    apply(transaction)
