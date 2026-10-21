from app.services.firestore import get_firestore_client
from app.services.workspace import fingerprint


def work_ref(uid: str, record_id: str, kind: str):
    return get_firestore_client().collection("work_items").document(fingerprint({"uid": uid, "id": record_id, "kind": kind}))


def enqueue(transaction, uid: str, record_id: str, kind: str, **details) -> None:
    transaction.set(work_ref(uid, record_id, kind), {"uid": uid, "id": record_id, "kind": kind, "status": "pending", **details})


def finish(uid: str, record_id: str, kind: str) -> None:
    work_ref(uid, record_id, kind).set({"uid": uid, "id": record_id, "kind": kind, "status": "complete"})
