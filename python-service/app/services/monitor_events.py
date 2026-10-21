"""Persist meaningful funding changes, ignoring duplicate and stale deliveries."""
from datetime import datetime, timedelta, timezone

from firebase_admin import firestore
from starlette.concurrency import run_in_threadpool

from app.models import Grant
from app.services.applications import emit_event, event_record
from app.services.firestore import _run_id, get_firestore_client, load_profile
from app.services.funding_changes import classify_change
from app.services.gemini import assess_grant
from app.services.monitors import load_watch
from app.services.tinyfish import FETCH_URL, UpstreamServiceError, _criteria_and_link, _public_https_url, _request, _response_json
from app.services.work_queue import finish
from app.services.workspace import collection, fingerprint, now_iso, opportunity_id


def text_key(value: str) -> str:
    return fingerprint({"text": " ".join(value.split())})


def public_result(item) -> bool:
    return isinstance(item, dict) and isinstance(item.get("url"), str) and _public_https_url(item["url"])


async def fresh_page(url: str) -> str:
    response = await _request("POST", FETCH_URL, timeout=30.0,
                              json={"urls": [url], "format": "markdown", "ttl": 0, "per_url_timeout_ms": 20000})
    payload = _response_json(response)
    results = payload.get("results")
    if payload.get("errors") or not isinstance(results, list) or not results or not isinstance(results[0], dict) or not isinstance(results[0].get("text"), str):
        raise UpstreamServiceError("Could not verify the current funding page. The last known requirements are preserved.")
    return results[0]["text"][:100000]


async def process_page(uid: str, watch: dict, payload: dict) -> None:
    results = payload.get("results", [])
    if not results or not public_result(results[0]) or opportunity_id(results[0]["url"]) != opportunity_id(watch["target"]):
        raise ValueError("Mismatched page result.")
    incoming = results[0].get("text")
    if not isinstance(incoming, str) or not incoming.strip():
        raise UpstreamServiceError("The funding page returned no readable content.")
    before = watch.get("baseline_text")
    if before is None:
        collection(uid, "watches").document(watch["id"]).update({"baseline_text": incoming[:100000], "last_checked_at": now_iso()})
        return
    if text_key(before) == text_key(incoming[:100000]):
        collection(uid, "watches").document(watch["id"]).update({"last_checked_at": now_iso(), "last_error": ""})
        return
    # Monitor callbacks have no authenticated history endpoint or reliable page timestamp.
    # Refetch the owned target so an older retry cannot roll the source back.
    after = await fresh_page(watch["target"])
    if text_key(before) == text_key(after):
        return
    change = await classify_change(before, after, watch["purpose"])
    watch_ref = collection(uid, "watches").document(watch["id"])
    grant_ref = collection(uid, "opportunities").document(watch["opportunity_id"])
    app_ref = collection(uid, "applications").document(watch["opportunity_id"])
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        current = watch_ref.get(transaction=transaction).to_dict()
        grant = grant_ref.get(transaction=transaction)
        application = app_ref.get(transaction=transaction)
        if current["status"] == "deleted":
            return
        if text_key(current.get("baseline_text") or "") != text_key(before):
            raise UpstreamServiceError("A newer monitor check is being processed. This event will be retried.")
        transaction.update(watch_ref, {"baseline_text": after, "last_checked_at": now_iso(), "last_error": ""})
        if not change.relevant:
            return
        if grant.exists:
            value = Grant.model_validate(grant.to_dict()).model_dump()
            criteria, _, _ = _criteria_and_link(after, watch["target"])
            value.update(clean_markdown=after, eligibility_criteria=[line[:2000] for line in criteria], inspection=None,
                         match_score=None, match_reason=None, eligibility_checks=[], checked_at=now_iso())
            value["source_version"] = fingerprint({key: value[key] for key in ("title", "application_url", "eligibility_criteria", "clean_markdown", "inspection")})
            transaction.set(grant_ref, value)
        if application.exists:
            transaction.update(app_ref, {"deadline_needs_review": True, "revision": application.to_dict().get("revision", 0) + 1})
        key = fingerprint({"watch": watch["id"], "run": payload["id"], "before": text_key(before), "after": text_key(after)})
        transaction.set(collection(uid, "events").document(key), {"id": key, **event_record(
            "funding_change", (grant.to_dict() or {}).get("title", "Funding programme changed"), change.summary,
            source_url=watch["target"], opportunity_id=watch["opportunity_id"], watch_id=watch["id"],
            requires_review=True, changed_fields=change.fields, quotes=change.quotes)})
    apply(transaction)


def store_new_opportunity(uid: str, grant: Grant, assessment: dict) -> bool:
    grant.id = opportunity_id(grant.source_url)
    grant.source_version = fingerprint(grant.model_dump(include={"title", "application_url", "eligibility_criteria", "clean_markdown", "inspection"}))
    reference = collection(uid, "opportunities").document(grant.id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def apply(transaction):
        if reference.get(transaction=transaction).exists:
            return False
        transaction.set(reference, {**grant.model_dump(), **assessment})
        transaction.set(collection(uid, "discovered_grants").document(_run_id(grant)), {
            "source_url": grant.source_url, "application_url": grant.application_url or grant.source_url, "discovered_at": now_iso()})
        key = fingerprint({"new_opportunity": grant.id})
        transaction.set(collection(uid, "events").document(key), {"id": key, **event_record(
            "new_opportunity", grant.title, "A funding watch found this page. Inspect the official application and confirm eligibility.",
            opportunity_id=grant.id, source_url=grant.source_url, requires_review=True)})
        return True
    return apply(transaction)


async def process_topic(uid: str, watch: dict, payload: dict) -> None:
    raw_results = payload.get("results", [])
    if not isinstance(raw_results, list):
        raise ValueError("Invalid topic result list.")
    results = [item for item in raw_results if public_result(item)]
    seen = set(watch.get("seen_urls", []))
    if not watch.get("baseline_ready"):
        seen.update(opportunity_id(item["url"]) for item in results)
        collection(uid, "watches").document(watch["id"]).update({"seen_urls": sorted(seen)[-2000:], "baseline_ready": True, "last_checked_at": now_iso(), "last_error": ""})
        return
    candidates = [item for item in results if opportunity_id(item["url"]) not in seen]
    if payload.get("is_baseline"):
        candidates = []
    if candidates:
        urls = list(dict.fromkeys(item["url"] for item in candidates))[:10]
        response = _response_json(await _request("POST", FETCH_URL, timeout=30.0,
            json={"urls": urls, "format": "html", "links": True, "ttl": 0, "per_url_timeout_ms": 20000}))
        pages = {item["url"]: item for item in response.get("results", []) if public_result(item)}
        try:
            profile = await run_in_threadpool(load_profile, uid)
        except LookupError:
            profile = None
        for item in candidates[:10]:
            page = pages.get(item["url"], {})
            html = page.get("text")
            if not isinstance(html, str) or len(html.strip()) < 40:
                continue
            criteria, application_url, markdown = _criteria_and_link(html[:250000], item["url"])
            grant = Grant(title=str(page.get("title") or item.get("title") or "Funding opportunity")[:300],
                          source_url=item["url"], application_url=application_url if application_url and _public_https_url(application_url) else None,
                          eligibility_criteria=[line[:2000] for line in criteria], clean_markdown=markdown, checked_at=now_iso())
            assessment = {}
            if profile:
                try:
                    assessment = (await assess_grant(profile, grant)).model_dump()
                    assessment["assessment_profile"] = fingerprint(profile.model_dump())
                except UpstreamServiceError:
                    pass
            await run_in_threadpool(store_new_opportunity, uid, grant, assessment)
        if response.get("errors"):
            raise UpstreamServiceError("Some new funding pages could not be fetched. They will be retried.")
    seen.update(opportunity_id(item["url"]) for item in results)
    collection(uid, "watches").document(watch["id"]).update({"seen_urls": sorted(seen)[-2000:], "last_checked_at": now_iso(), "last_error": ""})


async def process_monitor_event(uid: str, record_id: str) -> None:
    reference = collection(uid, "monitor_inbox").document(record_id)
    transaction = get_firestore_client().transaction()

    @firestore.transactional
    def claim(transaction):
        item = reference.get(transaction=transaction).to_dict()
        if item["status"] == "complete" or (item["status"] == "processing" and item.get("lease_until", "") > now_iso()):
            return item, False
        updates = {"status": "processing", "attempts": item["attempts"] + 1,
                   "lease_until": (datetime.now(timezone.utc) + timedelta(minutes=3)).isoformat()}
        transaction.update(reference, updates)
        return {**item, **updates}, True
    item, claimed = claim(transaction)
    if not claimed:
        if item["status"] == "complete":
            finish(uid, record_id, "monitor_event")
        return
    watch = load_watch(uid, item["watch_id"])
    try:
        payload = item["payload"]
        provider_id = payload.get("fetch_monitor_id") if watch["type"] == "fetch" else payload.get("search_monitor_id")
        if watch["status"] == "deleted" or not watch.get("monitor_id") or provider_id != watch["monitor_id"]:
            if watch["status"] in ("starting", "dispatching"):
                raise UpstreamServiceError("Waiting for monitor setup confirmation.")
        elif payload.get("errors") or payload.get("status_code", 200) != 200:
            raise UpstreamServiceError("TinyFish could not complete this monitor check. Last known data is preserved.")
        elif watch["type"] == "fetch":
            await process_page(uid, watch, payload)
        else:
            await process_topic(uid, watch, payload)
    except (UpstreamServiceError, ValueError) as error:
        collection(uid, "watches").document(watch["id"]).update({"last_error": str(error)})
        if item["attempts"] < 5:
            reference.update({"status": "pending"})
            return
        emit_event(uid, fingerprint({"watch_error": watch["id"], "run": record_id}), event_record(
            "watch_error", "Funding watch needs attention", str(error), source_url=watch["target"] if watch["type"] == "fetch" else "", requires_review=False))
    reference.update({"status": "complete"})
    finish(uid, record_id, "monitor_event")
