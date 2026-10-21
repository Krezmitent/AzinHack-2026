"""Run once from a scheduler, or keep the Docker worker running with --loop."""
import argparse
import asyncio
import logging

from google.cloud.firestore_v1.base_query import FieldFilter
from starlette.concurrency import run_in_threadpool

from app.services.firestore import get_firestore_client
from app.services.inspection_runs import refresh_inspection
from app.services.applications import deliver_reminder, due_reminders, record_submission
from app.services.monitors import setup_watch, check_watch
from app.services.monitor_events import process_monitor_event
from app.services.work_queue import finish

logger = logging.getLogger("autogrant.worker")


def pending_items() -> list[dict]:
    return [snapshot.to_dict() for snapshot in get_firestore_client().collection("work_items")
            .where(filter=FieldFilter("status", "==", "pending")).limit(50).stream()]


async def tick() -> None:
    semaphore = asyncio.Semaphore(3)

    async def process(item):
        async with semaphore:
            try:
                if item["kind"] == "inspection":
                    await refresh_inspection(item["uid"], item["id"])
                elif item["kind"] == "monitor_setup":
                    await setup_watch(item["uid"], item["watch_id"], item["id"])
                elif item["kind"] == "monitor_check":
                    await check_watch(item["uid"], item["watch_id"], item["id"])
                elif item["kind"] == "monitor_event":
                    await process_monitor_event(item["uid"], item["id"])
                elif item["kind"] == "application_run":
                    from app.main import application_run
                    result = await application_run(item["id"], uid=item["uid"])
                    await run_in_threadpool(record_submission, item["uid"], result["run"])
                    if result["run"]["status"] not in ("starting", "pending"):
                        await run_in_threadpool(finish, item["uid"], item["id"], item["kind"])
            except Exception:
                # Leave durable work pending after transient failures; log no profile text.
                logger.exception("Could not reconcile work item %s", item["id"])

    await asyncio.gather(*(process(item) for item in await run_in_threadpool(pending_items)))
    for reminder in await run_in_threadpool(due_reminders):
        await run_in_threadpool(deliver_reminder, reminder)


async def run(loop: bool) -> None:
    while True:
        await tick()
        if not loop:
            return
        await asyncio.sleep(30)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", action="store_true")
    asyncio.run(run(parser.parse_args().loop))
