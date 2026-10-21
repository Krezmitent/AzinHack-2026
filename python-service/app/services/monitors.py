"""Monitor ownership, bounded provisioning, and authenticated webhook ingestion."""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from firebase_admin import firestore

from app.config import settings
from app.services.firestore import get_firestore_client
from app.services.tinyfish import UpstreamServiceError, _headers, _public_https_url
from app.services.work_queue import enqueue, finish
from app.services.workspace import collection, fingerprint, load_opportunity, now_iso, opportunity_id

MONITOR_URL = "https://agent.tinyfish.ai/v1/monitors"
PUBLIC_FIELDS = {"id", "type", "target", "opportunity_id", "name", "cadence", "timezone", "purpose", "status", "monitor_id", "last_error", "last_checked_at", "check_status", "created_at"}


class MonitorError(UpstreamServiceError):
    def __init__(self, message, provider_status=None):
        super().__init__(message)
        self.provider_status = provider_status


async def monitor_request(method: str, path: str = "", body=None) -> dict:
    # No automatic retries: create and run-now are billed operations.
    try:
        async with httpx.AsyncClient(timeout=90.0 if method == "POST" else 20.0) as client:
            response = await client.request(method, MONITOR_URL + path, headers=_headers(), json=body)
    except httpx.RequestError as error:
        raise MonitorError("TinyFish monitor request timed out or could not be confirmed.") from error
    if method == "DELETE" and response.status_code in (200, 204, 404):
        return {}
    if response.status_code >= 400:
        raise MonitorError(f"TinyFish rejected the monitor request (HTTP {response.status_code}).", response.status_code)
    try:
        value = response.json()
        if not isinstance(value, dict):
            raise ValueError()
        return value
    except ValueError as error:
        raise MonitorError("TinyFish returned an invalid monitor response.") from error


def public_watch(value: dict) -> dict:
    return {key: item for key, item in value.items() if key in PUBLIC_FIELDS}


def load_watch(uid: str, record_id: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{64}", record_id):
        raise LookupError("Watch not found.")
    snapshot = collection(uid, "watches").document(record_id).get()
    if not snapshot.exists:
        raise LookupError("Watch not found.")
    return snapshot.to_dict()


def reserve_watch(uid: str, request) -> dict:
    base = settings.public_webhook_base_url.rstrip("/")
    if not settings.tinyfish_api_key or not _public_https_url(base) or urlparse(base).path or urlparse(base).query or urlparse(base).fragment:
        raise UpstreamServiceError("Configure TinyFish and a public HTTPS webhook origin before enabling funding watches.", 503)
    target = load_opportunity(uid, request.opportunity_id or "")["source_url"] if request.type == "fetch" else request.query.strip()
    if not target or not request.purpose.strip() or (request.type == "fetch" and not _public_https_url(target)):
        raise ValueError("Choose a public HTTPS opportunity page or a nonblank search query.")
    record_id = fingerprint({"type": request.type, "target": opportunity_id(target) if request.type == "fetch" else target.casefold()})
    reference = collection(uid, "watches").document(record_id)
    quota_ref = collection(uid, "settings").document("monitor_quota")
    global_quota_ref = get_firestore_client().collection("system").document("monitor_quota")
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        current = reference.get(transaction=transaction)
        quota = quota_ref.get(transaction=transaction)
        global_quota = global_quota_ref.get(transaction=transaction)
        if current.exists and current.to_dict()["status"] != "deleted":
            return current.to_dict()
        count = (quota.to_dict() or {}).get("count", 0)
        total = (global_quota.to_dict() or {}).get("count", 0)
        if count >= settings.max_monitors_per_user or total >= 50:
            raise ValueError("The watch limit has been reached. Delete an unused watch before adding another.")
        callback_id, secret = uuid4().hex, secrets.token_urlsafe(32)
        record = {"id": record_id, "type": request.type, "target": target, "opportunity_id": request.opportunity_id,
                  "name": f"AutoGrant-{callback_id}", "cadence": request.cadence, "timezone": request.timezone,
                  "purpose": request.purpose, "status": "starting", "monitor_id": None, "created_at": now_iso(),
                  "callback_id": callback_id, "callback_secret": secret, "webhook_base": base,
                  "last_error": "", "last_checked_at": None, "check_status": None, "baseline_text": None, "seen_urls": []}
        record["baseline_ready"] = False
        transaction.set(reference, record)
        transaction.set(quota_ref, {"count": count + 1})
        transaction.set(global_quota_ref, {"count": total + 1})
        transaction.set(get_firestore_client().collection("monitor_callbacks").document(callback_id), {
            "uid": uid, "watch_id": record_id, "secret_hash": hashlib.sha256(secret.encode()).hexdigest()})
        enqueue(transaction, uid, callback_id, "monitor_setup", watch_id=record_id)
        return record
    return apply(transaction)


def seed_baseline(record: dict, run: dict) -> dict:
    results = run.get("results", [])
    if run.get("errors") or not isinstance(results, list):
        return {"last_error": "TinyFish could not capture the first baseline. The next successful check will establish it."}
    if record["type"] == "fetch":
        text = results[0].get("text", "") if results and isinstance(results[0], dict) else ""
        return {"baseline_text": text[:100000] if isinstance(text, str) and text.strip() else None,
                "baseline_ready": bool(isinstance(text, str) and text.strip())}
    return {"seen_urls": [opportunity_id(item["url"]) for item in results if isinstance(item, dict) and isinstance(item.get("url"), str) and _public_https_url(item["url"])],
            "baseline_ready": True}


def activate_watch(uid: str, record_id: str, remote: dict, run: dict | None = None, callback_id: str | None = None) -> dict:
    record = load_watch(uid, record_id)
    if record["status"] == "deleted":
        return record
    monitor_id = remote.get("id")
    config = remote.get("config", {})
    target = config.get("url") if record["type"] == "fetch" else config.get("query")
    if (not isinstance(monitor_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", monitor_id)
            or remote.get("type") != record["type"] or target != record["target"] or remote.get("name") != record["name"]):
        raise MonitorError("TinyFish returned a mismatched monitor configuration.")
    updates = {"monitor_id": monitor_id, "status": remote.get("status", "active"), "last_error": ""}
    if run is not None:
        updates.update(seed_baseline(record, run))
    reference = collection(uid, "watches").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        current = reference.get(transaction=transaction).to_dict()
        if current["status"] == "deleted" or (callback_id and current["callback_id"] != callback_id):
            return current
        transaction.update(reference, updates)
        return {**current, **updates}
    return apply(transaction)


async def setup_watch(uid: str, record_id: str, callback_id: str) -> None:
    reference = collection(uid, "watches").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def claim(transaction):
        record = reference.get(transaction=transaction).to_dict()
        if record["callback_id"] != callback_id or record["status"] != "starting":
            return record, False
        transaction.update(reference, {"status": "dispatching", "setup_started_at": now_iso()})
        return {**record, "status": "dispatching", "setup_started_at": now_iso()}, True
    record, claimed = claim(transaction)
    if record["callback_id"] != callback_id:
        finish(uid, callback_id, "monitor_setup")
        return
    if claimed:
        cron = "0 9 * * *" if record["cadence"] == "daily" else "0 */6 * * *"
        config = {"url": record["target"], "format": "markdown"} if record["type"] == "fetch" else {"query": record["target"], "recency_minutes": 2880, "result_limit": 10}
        try:
            response = await monitor_request("POST", body={"type": record["type"], "name": record["name"], "config": config,
                "schedule_cron": f"CRON_TZ={record['timezone']} {cron}", "purpose": record["purpose"],
                "webhook_url": f"{record['webhook_base']}/api/tinyfish/monitor/{record['callback_id']}/{record['callback_secret']}"})
            activate_watch(uid, record_id, response.get("monitor", {}), response.get("run", {}), callback_id)
            finish(uid, callback_id, "monitor_setup")
            return
        except MonitorError as error:
            known_rejection = error.provider_status in (400, 401, 402, 403, 422)
            reference.update({"status": "failed" if known_rejection else "dispatching", "last_error": str(error)})
            if known_rejection:
                finish(uid, callback_id, "monitor_setup")
            return
    if record["status"] == "dispatching":
        try:
            response = await monitor_request("GET")
        except MonitorError:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(record["setup_started_at"])).total_seconds() > 300:
                reference.update({"status": "unknown", "last_error": "Setup is unconfirmed. Restore TinyFish access and sync this watch."})
                finish(uid, callback_id, "monitor_setup")
            return
        matches = [value for value in response.get("monitors", []) if value.get("name") == record["name"]]
        if matches:
            activate_watch(uid, record_id, matches[0], callback_id=callback_id)
            finish(uid, callback_id, "monitor_setup")
        elif (datetime.now(timezone.utc) - datetime.fromisoformat(record["setup_started_at"])).total_seconds() > 300:
            reference.update({"status": "unknown", "last_error": "Setup could not be confirmed. Sync with TinyFish before creating another watch."})
            finish(uid, callback_id, "monitor_setup")
    else:
        finish(uid, callback_id, "monitor_setup")


def release_watch(uid: str, record_id: str, callback_id: str) -> dict:
    reference = collection(uid, "watches").document(record_id)
    quotas = [collection(uid, "settings").document("monitor_quota"), get_firestore_client().collection("system").document("monitor_quota")]
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        record = reference.get(transaction=transaction).to_dict()
        counts = [(ref, ref.get(transaction=transaction)) for ref in quotas]
        if record["status"] == "deleted" or record.get("callback_id") != callback_id:
            return record
        transaction.update(reference, {"status": "deleted"})
        for ref, snapshot in counts:
            transaction.set(ref, {"count": max(0, (snapshot.to_dict() or {}).get("count", 0) - 1)})
        return {**record, "status": "deleted"}
    return apply(transaction)


def queue_check(uid: str, record_id: str) -> dict:
    reference = collection(uid, "watches").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        record = reference.get(transaction=transaction).to_dict()
        if record.get("status") not in ("active", "paused") or not record.get("monitor_id"):
            raise ValueError("Wait for the TinyFish monitor to become available before checking it.")
        if record.get("check_status") in ("queued", "running"):
            return record
        check_id = uuid4().hex
        transaction.update(reference, {"check_status": "queued", "check_requested_at": now_iso(), "check_id": check_id})
        enqueue(transaction, uid, check_id, "monitor_check", watch_id=record_id)
        return {**record, "check_status": "queued", "check_id": check_id}
    return apply(transaction)


async def watch_action(uid: str, record_id: str, action: str) -> dict:
    record = load_watch(uid, record_id)
    if record["status"] == "deleted":
        return record
    if action == "sync" and not record.get("monitor_id"):
        response = await monitor_request("GET")
        match = next((value for value in response.get("monitors", []) if value.get("name") == record["name"]), None)
        if not match:
            raise ValueError("No matching TinyFish monitor was found. Check the TinyFish dashboard before recreating it.")
        return activate_watch(uid, record_id, match)
    if not record.get("monitor_id"):
        if action == "delete" and record["status"] == "failed":
            return release_watch(uid, record_id, record["callback_id"])
        raise ValueError("Wait for setup or sync the watch before changing it.")
    path = f"/{record['monitor_id']}"
    if action == "check":
        return queue_check(uid, record_id)
    if action == "delete":
        await monitor_request("DELETE", path)
        return release_watch(uid, record_id, record["callback_id"])
    if action == "sync":
        response = await monitor_request("GET", path)
        remote = response.get("monitor", response)
        return activate_watch(uid, record_id, remote)
    status = "paused" if action == "pause" else "active"
    await monitor_request("PATCH", path, {"status": status})
    reference = collection(uid, "watches").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        current = reference.get(transaction=transaction).to_dict()
        if current.get("status") == "deleted" or current.get("callback_id") != record.get("callback_id") or current.get("monitor_id") != record.get("monitor_id"):
            return current
        transaction.update(reference, {"status": status})
        return {**current, "status": status}
    return apply(transaction)


def authenticate_callback(callback_id: str, secret: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{32}", callback_id) or not re.fullmatch(r"[A-Za-z0-9_-]{43}", secret):
        raise PermissionError("Invalid callback.")
    snapshot = get_firestore_client().collection("monitor_callbacks").document(callback_id).get()
    if not snapshot.exists or not hmac.compare_digest(snapshot.to_dict()["secret_hash"], hashlib.sha256(secret.encode()).hexdigest()):
        raise PermissionError("Invalid callback.")
    value = snapshot.to_dict()
    watch = load_watch(value["uid"], value["watch_id"])
    if watch["callback_id"] != callback_id or watch["status"] == "deleted":
        raise PermissionError("Inactive callback.")
    return value


def enqueue_run(uid: str, watch_id: str, payload: dict) -> str:
    record = load_watch(uid, watch_id)
    provider_id = payload.get("fetch_monitor_id") if record["type"] == "fetch" else payload.get("search_monitor_id")
    if record.get("monitor_id") and provider_id != record["monitor_id"]:
        raise ValueError("Mismatched monitor callback.")
    run_id = payload.get("id")
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", run_id):
        raise ValueError("Invalid monitor run ID.")
    key = fingerprint({"watch": watch_id, "provider": provider_id, "run": run_id})
    reference = collection(uid, "monitor_inbox").document(key)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        if reference.get(transaction=transaction).exists:
            return key
        transaction.set(reference, {"id": key, "watch_id": watch_id, "payload": payload, "status": "pending", "attempts": 0})
        enqueue(transaction, uid, key, "monitor_event")
        return key
    return apply(transaction)


async def check_watch(uid: str, record_id: str, check_id: str) -> None:
    reference = collection(uid, "watches").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def claim(transaction):
        record = reference.get(transaction=transaction).to_dict()
        if record.get("check_id") != check_id or record.get("check_status") != "queued" or record["status"] == "deleted":
            return record, False
        transaction.update(reference, {"check_status": "running", "check_started_at": now_iso()})
        return {**record, "check_status": "running", "check_started_at": now_iso()}, True
    record, claimed = claim(transaction)
    if record.get("check_id") != check_id or record["status"] == "deleted":
        finish(uid, check_id, "monitor_check")
        return
    if claimed:
        try:
            response = await monitor_request("POST", f"/{record['monitor_id']}/runs")
            payload = response.get("run", {})
            payload["fetch_monitor_id" if record["type"] == "fetch" else "search_monitor_id"] = record["monitor_id"]
            enqueue_run(uid, record_id, payload)
            reference.update({"check_status": None, "last_error": ""})
        except (MonitorError, ValueError) as error:
            reference.update({"check_status": "unknown", "last_error": str(error)})
        finish(uid, check_id, "monitor_check")
    elif record.get("check_status") != "running" or (datetime.now(timezone.utc) - datetime.fromisoformat(record["check_started_at"])).total_seconds() > 180:
        if record.get("check_status") == "running":
            reference.update({"check_status": "unknown", "last_error": "Could not confirm the manual check. A scheduled check will reconcile future changes."})
        finish(uid, check_id, "monitor_check")
