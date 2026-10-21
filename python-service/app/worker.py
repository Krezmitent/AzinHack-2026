"""Run once from a scheduler, or keep the Docker worker running with --loop."""
import argparse
import asyncio
import logging

from google.cloud.firestore_v1.base_query import FieldFilter
from starlette.concurrency import run_in_threadpool

from app.services.firestore import get_firestore_client
from app.services.inspection_runs import refresh_inspection

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
            except Exception:
                # Leave durable work pending after transient failures; log no profile text.
                logger.exception("Could not reconcile work item %s", item["id"])

    await asyncio.gather(*(process(item) for item in await run_in_threadpool(pending_items)))


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
