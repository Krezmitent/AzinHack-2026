import unittest
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from app.config import settings
from app.monitor_models import WatchRequest
from app.models import Grant
from app.services import applications, funding_changes, monitor_events, monitors, work_queue, workspace
from app.services.tinyfish import UpstreamServiceError
from fakes import MemoryFirestore


class MonitorTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MemoryFirestore()
        self.patches = [patch.object(module, "get_firestore_client", return_value=self.db)
                        for module in (workspace, monitors, work_queue, monitor_events, applications)]
        self.patches += [patch.object(workspace.firestore, "transactional", side_effect=lambda fn: fn),
                         patch.object(monitors.settings, "tinyfish_api_key", "test"),
                         patch.object(monitors.settings, "public_webhook_base_url", "https://app.example.com")]
        for item in self.patches:
            item.start()
        self.grant = Grant(title="Climate fund", source_url="https://example.org/grant", clean_markdown="Funding page")
        workspace.save_opportunities("alice", [self.grant])

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def test_timezone_validation_rejects_unknown_zone(self):
        with self.assertRaises(ValidationError):
            WatchRequest(type="fetch", opportunity_id=self.grant.id, timezone="Mars/Olympus")

    def test_watch_creation_is_idempotent_and_owner_scoped(self):
        request = WatchRequest(type="fetch", opportunity_id=self.grant.id)
        first = monitors.reserve_watch("alice", request)
        second = monitors.reserve_watch("alice", request)
        self.assertEqual(first["callback_id"], second["callback_id"])
        self.assertEqual(self.db.data["users/alice/settings/monitor_quota"]["count"], 1)
        with self.assertRaises(LookupError):
            monitors.load_watch("bob", first["id"])

    async def test_ambiguous_monitor_create_is_reconciled_without_second_post(self):
        record = monitors.reserve_watch("alice", WatchRequest(type="fetch", opportunity_id=self.grant.id))
        post_error = monitors.MonitorError("uncertain"); post_error.provider_status = None
        with patch.object(monitors, "monitor_request", new=AsyncMock(side_effect=[post_error, {"monitors": []}])) as request:
            await monitors.setup_watch("alice", record["id"], record["callback_id"])
            await monitors.setup_watch("alice", record["id"], record["callback_id"])
        self.assertEqual(request.await_args_list[0].args[0], "POST")
        self.assertEqual(request.await_args_list[1].args[0], "GET")
        self.assertEqual(len([args for args in request.await_args_list if args.args[0] == "POST"]), 1)

    async def test_topic_first_result_is_quiet_baseline(self):
        watch = {"id": "watch", "type": "search", "target": "climate grants", "seen_urls": [], "baseline_ready": False}
        self.db.collection("users").document("alice").collection("watches").document("watch").set(watch)
        payload = {"results": [{"url": "https://example.org/new", "title": "New grant"}]}
        await monitor_events.process_topic("alice", watch, payload)
        self.assertEqual(self.db.data["users/alice/watches/watch"]["seen_urls"], [workspace.opportunity_id("https://example.org/new")])
        self.assertEqual([path for path in self.db.data if "/events/" in path], [])

    async def test_unverified_change_quote_is_rejected(self):
        with patch.object(funding_changes, "_generate", new=AsyncMock(return_value={"response": "{}"})):
            with patch.object(funding_changes, "_json", return_value={"relevant": True, "summary": "Deadline changed", "fields": ["deadline"], "quotes": ["Invented text"]}):
                with self.assertRaises(UpstreamServiceError):
                    await funding_changes.classify_change("deadline 1", "deadline 2", "funding")


if __name__ == "__main__":
    unittest.main()
