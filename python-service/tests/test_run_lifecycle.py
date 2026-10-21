import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import httpx
from fastapi.security import HTTPAuthorizationCredentials

from app import main as main_module
from app.auth import _verify_token, authenticated_uid, authenticated_uid_for_execution
from app.services.tinyfish import UpstreamServiceError


GRANT = {
    "title": "Demo grant", "source_url": "https://grants.example.org/demo",
    "application_url": "https://grants.example.org/apply", "eligibility_criteria": [],
    "clean_markdown": "Eligibility terms",
}
BODY = {"grant": GRANT, "drafted_answers": {"Why?": "Because."}, "confirm_submit": True}
RECORD_ID = "a" * 64


class RunLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        main_module.app.dependency_overrides[authenticated_uid_for_execution] = lambda: "alice"
        self.records = {}
        self.started = 0

        def reserve(uid, grant):
            key = (uid, RECORD_ID)
            if key in self.records:
                return self.records[key].copy(), False
            record = {
                "id": RECORD_ID, "grant_title": grant.title, "source_url": grant.source_url,
                "application_url": grant.application_url, "status": "starting",
                "message": "Preparing the application run.", "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(), "run_id": None,
            }
            self.records[key] = record
            return record.copy(), True

        def update(uid, record_id, changes):
            record = self.records[(uid, record_id)]
            if record["status"] not in ("submitted", "not_submitted", "unknown"):
                record.update(changes)
            return record.copy()

        def load(uid, record_id):
            try:
                return self.records[(uid, record_id)].copy()
            except KeyError as error:
                raise LookupError("Application run was not found.") from error

        self.patches = [
            patch.object(main_module, "reviewed_grant", side_effect=lambda uid, request: request.grant),
            patch.object(main_module.settings, "tinyfish_api_key", "test-key"),
            patch.object(main_module, "grant_was_discovered", return_value=True),
            patch.object(main_module, "reserve_application_run", side_effect=reserve),
            patch.object(main_module, "update_application_run", side_effect=update),
            patch.object(main_module, "load_application_run", side_effect=load),
            patch.object(main_module, "list_application_runs", side_effect=lambda uid: [value.copy() for (owner, _), value in self.records.items() if owner == uid]),
            patch.object(main_module, "start_web_agent", new_callable=AsyncMock, return_value="run-1"),
            patch.object(main_module, "get_web_agent_run", new_callable=AsyncMock,
                         return_value={"run_id": "run-1", "status": "pending", "provider_status": "RUNNING", "message": "Still running."}),
        ]
        for item in self.patches:
            item.start()
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=main_module.app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()
        for item in reversed(self.patches):
            item.stop()
        main_module.app.dependency_overrides.clear()

    async def test_repeat_start_returns_same_record_without_second_provider_call(self):
        first = await self.client.post("/api/execute-application", json=BODY)
        second = await self.client.post("/api/execute-application", json=BODY)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["run"]["status"], "pending")
        self.assertEqual(second.json()["run"]["id"], RECORD_ID)
        self.assertEqual(main_module.start_web_agent.await_count, 1)
        self.assertNotIn("drafted_answers", self.records[("alice", RECORD_ID)])

    async def test_status_poll_progresses_only_with_provider_evidence(self):
        await self.client.post("/api/execute-application", json=BODY)
        pending = await self.client.get(f"/api/application-runs/{RECORD_ID}")
        self.assertEqual(pending.json()["run"]["status"], "pending")
        main_module.get_web_agent_run.return_value = {
            "run_id": "run-1", "status": "submitted", "provider_status": "COMPLETED",
            "evidence": "CONFIRM-42", "message": "Confirmation evidence reported.",
        }
        confirmed = await self.client.get(f"/api/application-runs/{RECORD_ID}")
        self.assertEqual(confirmed.json()["run"]["evidence"], "CONFIRM-42")
        again = await self.client.get(f"/api/application-runs/{RECORD_ID}")
        self.assertEqual(again.json()["run"]["status"], "submitted")
        self.assertEqual(main_module.get_web_agent_run.await_count, 2)

    async def test_ambiguous_start_error_is_saved_and_never_retried(self):
        main_module.start_web_agent.side_effect = UpstreamServiceError("Timed out.")
        first = await self.client.post("/api/execute-application", json=BODY)
        second = await self.client.post("/api/execute-application", json=BODY)
        self.assertEqual(first.json()["run"]["status"], "unknown")
        self.assertEqual(second.json()["run"]["status"], "unknown")
        self.assertEqual(main_module.start_web_agent.await_count, 1)

    async def test_requires_discovered_grant_and_owner_scoped_status(self):
        main_module.grant_was_discovered.return_value = False
        blocked = await self.client.post("/api/execute-application", json=BODY)
        self.assertEqual(blocked.status_code, 403)
        self.assertEqual(main_module.start_web_agent.await_count, 0)
        main_module.grant_was_discovered.return_value = True
        await self.client.post("/api/execute-application", json=BODY)
        main_module.app.dependency_overrides[authenticated_uid_for_execution] = lambda: "bob"
        foreign = await self.client.get(f"/api/application-runs/{RECORD_ID}")
        self.assertEqual(foreign.status_code, 404)

    async def test_invalid_target_and_confirmation_fail_before_reservation(self):
        no_confirmation = await self.client.post("/api/execute-application", json={**BODY, "confirm_submit": False})
        self.assertEqual(no_confirmation.status_code, 400)
        invalid = await self.client.post("/api/execute-application", json={**BODY, "grant": {**GRANT, "application_url": "http://localhost/apply"}})
        self.assertEqual(invalid.status_code, 422)
        self.assertEqual(len(self.records), 0)

    async def test_discovery_uses_location_and_rejects_blank_location(self):
        main_module.app.dependency_overrides[authenticated_uid] = lambda: "alice"
        with patch.object(main_module, "discover_and_parse_grants", new_callable=AsyncMock, return_value=[]) as discover, patch.object(main_module, "record_discovered_grants") as record:
            blank = await self.client.post("/api/discover-grants", json={"location": "   ", "sector": "Climate tech"})
            self.assertEqual(blank.status_code, 422)
            blank_sector = await self.client.post("/api/discover-grants", json={"location": "India", "sector": "   "})
            self.assertEqual(blank_sector.status_code, 422)
            valid = await self.client.post("/api/discover-grants", json={"location": " India ", "sector": "Climate tech"})
            self.assertEqual(valid.status_code, 200)
            discover.assert_awaited_once_with("India", "Climate tech")
            record.assert_called_once_with("alice", [])


class AuthTests(unittest.TestCase):
    def test_email_verification_required_after_token_validation(self):
        bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
        with patch("app.auth.get_admin_app", return_value=object()), patch("app.auth.auth.verify_id_token", return_value={"uid": "alice", "email_verified": False}):
            from fastapi import HTTPException
            with self.assertRaises(HTTPException) as result:
                _verify_token(bearer)
            self.assertEqual(result.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
