import unittest
from unittest.mock import AsyncMock, patch

import httpx

from app import main
from app.auth import authenticated_uid
from app.models import Grant, StartupProfile
from app.services import gemini, workspace
from fakes import MemoryFirestore

PROFILE = StartupProfile(sector="Climate", location="India", revenue="Pre-revenue", demographics="",
                         pitchDeckText="We build affordable energy storage.")


class WorkspaceTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = MemoryFirestore()
        self.patches = [patch.object(workspace, "get_firestore_client", return_value=self.db),
                        patch.object(workspace.firestore, "transactional", side_effect=lambda function: function)]
        for item in self.patches:
            item.start()
        self.grant = Grant(title="Climate fund", source_url="https://example.org/grant", clean_markdown="Open to incorporated companies")
        workspace.save_opportunities("alice", [self.grant])
        main.app.dependency_overrides[authenticated_uid] = lambda: "alice"
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=main.app), base_url="http://test")
        self.body = {"answers": {"Why?": "Energy storage."}, "profile": PROFILE.model_dump(),
                     "source_version": self.grant.source_version, "expected_revision": 0}

    async def asyncTearDown(self):
        await self.client.aclose()
        main.app.dependency_overrides.clear()
        for item in reversed(self.patches):
            item.stop()

    async def test_reload_restores_opportunity_and_versioned_draft(self):
        first = await self.client.post(f"/api/workspace/drafts/{self.grant.id}", json=self.body)
        self.assertEqual(first.status_code, 200, first.text)
        response = await self.client.get("/api/workspace")
        self.assertEqual(response.json()["opportunities"][0]["title"], "Climate fund")
        self.assertEqual(response.json()["drafts"][0]["answers"], self.body["answers"])
        second = await self.client.post(f"/api/workspace/drafts/{self.grant.id}", json={**self.body, "expected_revision": 1, "answers": {"Why?": "Edited."}})
        self.assertEqual(second.json()["draft"]["revision"], 2)
        history = self.db.data[f"users/alice/drafts/{self.grant.id}/revisions/1"]
        self.assertEqual(history["answers"], self.body["answers"])

    async def test_stale_tab_cannot_overwrite_draft(self):
        url = f"/api/workspace/drafts/{self.grant.id}"
        await self.client.post(url, json=self.body)
        stale = await self.client.post(url, json={**self.body, "answers": {"Why?": "Stale tab."}})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(workspace.list_workspace("alice")["drafts"][0]["answers"], self.body["answers"])

    async def test_source_change_preserves_draft_and_requires_review(self):
        url = f"/api/workspace/drafts/{self.grant.id}"
        await self.client.post(url, json=self.body)
        self.grant.clean_markdown = "Now only open to established companies"
        workspace.save_opportunities("alice", [self.grant])
        stale = await self.client.post(url, json={**self.body, "expected_revision": 1})
        self.assertEqual(stale.status_code, 409)
        self.assertEqual(workspace.list_workspace("alice")["drafts"][0]["source_version"], self.body["source_version"])

    async def test_workspace_and_drafts_are_owner_scoped(self):
        main.app.dependency_overrides[authenticated_uid] = lambda: "bob"
        self.assertEqual((await self.client.get("/api/workspace")).json()["opportunities"], [])
        denied = await self.client.post(f"/api/workspace/drafts/{self.grant.id}", json=self.body)
        self.assertEqual(denied.status_code, 404)

    async def test_invalid_draft_is_rejected(self):
        response = await self.client.post(f"/api/workspace/drafts/{self.grant.id}", json={**self.body, "answers": {"Why?": " "}})
        self.assertEqual(response.status_code, 422)

    async def test_assessment_keeps_missing_evidence_unknown(self):
        result = '{"score":72,"reason":"Relevant sector.","eligibility_checks":[{"criterion":"Incorporated","status":"unknown","reason":"Incorporation not provided."}]}'
        with patch.object(gemini, "_generate", new=AsyncMock(return_value=result)):
            assessment = await gemini.assess_grant(PROFILE, self.grant)
        self.assertEqual(assessment.eligibility_checks[0].status, "unknown")
        workspace.save_assessment("alice", self.grant, assessment.model_dump(), PROFILE)
        self.assertEqual(workspace.load_opportunity("alice", self.grant.id)["match_score"], 72)

    def test_canonical_identity_ignores_tracking_but_preserves_round(self):
        self.assertEqual(workspace.opportunity_id("https://example.org/grant?utm_source=mail#apply"), self.grant.id)
        self.assertNotEqual(workspace.opportunity_id("https://example.org/grant?round=2027"), self.grant.id)

    def test_changed_profile_hides_old_assessment_on_reload(self):
        self.db.collection("users").document("alice").set(PROFILE.model_dump())
        workspace.save_assessment("alice", self.grant, {"match_score": 80}, PROFILE)
        self.assertEqual(workspace.list_workspace("alice")["opportunities"][0]["match_score"], 80)
        self.db.collection("users").document("alice").update({"location": "Germany"})
        self.assertIsNone(workspace.list_workspace("alice")["opportunities"][0]["match_score"])

    def test_assessment_cannot_overwrite_a_new_source_version(self):
        old = self.grant.model_copy(deep=True)
        self.grant.clean_markdown = "Changed requirements"
        workspace.save_opportunities("alice", [self.grant])
        with self.assertRaises(ValueError):
            workspace.save_assessment("alice", old, {"match_score": 80}, PROFILE)
