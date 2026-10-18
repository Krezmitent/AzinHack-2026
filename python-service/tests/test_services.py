import asyncio
import unittest
from unittest.mock import AsyncMock, patch

import httpx
from pydantic import ValidationError

from app.models import ExecuteApplicationRequest, Grant, StartupProfile
from app.services import gemini, tinyfish


PROFILE = StartupProfile(
    sector="Climate tech", location="India", revenue="Pre-revenue", demographics="Indian founders",
    pitchDeckText="We build affordable clean energy storage for local businesses.",
)
GRANT = Grant(title="Demo grant", source_url="https://grants.example.org/demo",
              application_url="https://grants.example.org/apply", eligibility_criteria=["US startup"])


class ServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_score_and_draft_build_valid_prompts(self):
        with patch.object(gemini, "_generate", new=AsyncMock(return_value='{"score": 84, "reason": "Sector fits."}')) as generate:
            self.assertEqual(await gemini.score_grant(PROFILE, GRANT), (84, "Sector fits."))
            self.assertIn('"eligibility_criteria"', generate.call_args.args[0])

        with patch.object(gemini, "_generate", new=AsyncMock(return_value='{"answers": {"Why?": "Because."}}')):
            answers = await gemini.draft_answers(PROFILE, GRANT, ["Why?", "How?"])
            self.assertEqual(answers["Why?"], "Because.")
            self.assertTrue(answers["How?"].startswith("Information not provided;"))

        long_profile = PROFILE.model_copy(update={"pitchDeckText": "X" * 30_000})
        with patch.object(gemini, "_generate", new=AsyncMock(return_value='{"score": 84, "reason": "Sector fits."}')) as generate:
            await gemini.score_grant(long_profile, GRANT)
            self.assertLess(len(generate.call_args.args[0]), 10_000)

    async def test_malformed_gemini_output_is_reported_as_upstream_error(self):
        with patch.object(gemini, "_generate", new=AsyncMock(return_value="not-json")):
            with self.assertRaises(tinyfish.UpstreamServiceError):
                await gemini.score_grant(PROFILE, GRANT)
        with patch.object(gemini, "_generate", new=AsyncMock(return_value='{"score": true, "reason": "yes"}')):
            with self.assertRaises(tinyfish.UpstreamServiceError):
                await gemini.score_grant(PROFILE, GRANT)

    async def test_agent_start_is_never_retried_and_status_needs_confirmation(self):
        response = httpx.Response(200, json={"run_id": "run-1", "error": None})
        with patch.object(tinyfish, "_request", new=AsyncMock(return_value=response)) as request:
            run_id = await tinyfish.start_web_agent("https://grants.example.org/apply", {"Why?": "Because."}, [])
            self.assertEqual(run_id, "run-1")
            self.assertEqual(request.call_args.kwargs["retry"], False)
            self.assertEqual(request.call_args.args[1], tinyfish.AGENT_URL)
            self.assertNotIn("credentials", request.call_args.kwargs["json"])
            self.assertEqual(request.call_args.kwargs["json"]["output_schema"]["properties"]["submitted"]["type"], "boolean")

        response = httpx.Response(200, json={"status": "COMPLETED", "run_id": "run-1", "result": {"submitted": True}})
        with patch.object(tinyfish, "_request", new=AsyncMock(return_value=response)):
            result = await tinyfish.get_web_agent_run("run-1")
            self.assertEqual(result["status"], "unknown")

        response = httpx.Response(200, json={"status": "COMPLETED", "run_id": "run-1", "result": {"submitted": True, "confirmation_number": "ABC-42"}})
        with patch.object(tinyfish, "_request", new=AsyncMock(return_value=response)):
            result = await tinyfish.get_web_agent_run("run-1")
            self.assertEqual(result["status"], "submitted")
            self.assertEqual(result["evidence"], "ABC-42")

        response = httpx.Response(200, json={"status": "RUNNING", "run_id": "run-1", "result": None})
        with patch.object(tinyfish, "_request", new=AsyncMock(return_value=response)):
            self.assertEqual((await tinyfish.get_web_agent_run("run-1"))["status"], "pending")

    async def test_failed_agent_post_has_one_attempt(self):
        class FailingClient:
            calls = 0

            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def request(self, *_args, **_kwargs):
                self.calls += 1
                return httpx.Response(503, json={"error": "unavailable"})

        client = FailingClient()
        with patch.object(tinyfish, "_headers", return_value={"X-API-Key": "test"}), patch.object(tinyfish.httpx, "AsyncClient", return_value=client):
            with self.assertRaises(tinyfish.UpstreamServiceError):
                await tinyfish._request("POST", tinyfish.AGENT_URL, retry=False)
        self.assertEqual(client.calls, 1)

    async def test_rejects_local_or_insecure_agent_targets(self):
        for url in ("http://grants.example.org/apply", "https://localhost/apply", "https://127.0.0.1/apply",
                    "https://10.1.2.3/apply", "https://localhost./apply", "https://user:pass@grants.example.org/apply"):
            with self.subTest(url=url), self.assertRaises(tinyfish.UpstreamServiceError):
                await tinyfish.start_web_agent(url, {"Why?": "Because."}, [])

    async def test_vault_is_disabled_until_each_user_has_owned_credentials(self):
        with self.assertRaises(tinyfish.UpstreamServiceError):
            await tinyfish.start_web_agent("https://grants.example.org/apply", {"Why?": "Because."}, ["friendly label"])
        response = httpx.Response(200, json={"run_id": "run-3", "error": None})
        with patch.object(tinyfish, "_request", new=AsyncMock(return_value=response)) as request:
            await tinyfish.start_web_agent("https://grants.example.org/apply", {"Why?": "Because."}, [])
            payload = request.call_args.kwargs["json"]
            self.assertNotIn("credential_item_ids", payload)
            self.assertFalse(payload["use_vault"])

    async def test_discovery_cache_reuses_successful_result(self):
        tinyfish._discovery_cache.clear()
        with patch.object(tinyfish, "_discover_uncached", new=AsyncMock(return_value=[GRANT])) as discover:
            first, second = await asyncio.gather(tinyfish.discover_and_parse_grants("India", "Climate tech"), tinyfish.discover_and_parse_grants(" india ", "CLIMATE TECH"))
            self.assertEqual(discover.await_count, 1)
            self.assertEqual(first[0].title, second[0].title)
            self.assertIsNot(first[0], second[0])
            await tinyfish.discover_and_parse_grants("Brazil", "Climate tech")
            self.assertEqual(discover.await_count, 2)
            await tinyfish.discover_and_parse_grants("India", "Health tech")
            self.assertEqual(discover.await_count, 3)
        tinyfish._discovery_cache.clear()

    async def test_search_uses_founder_location_without_us_bias(self):
        response = httpx.Response(200, json={"results": []})
        with patch.object(tinyfish, "_request", new=AsyncMock(return_value=response)) as request:
            self.assertEqual(await tinyfish.search_grants("India", "Climate tech"), [])
            params = request.call_args.kwargs["params"]
            self.assertIn("India", params["query"])
            self.assertIn("Climate tech", params["query"])
            self.assertNotIn("location", params)

    def test_execute_payload_size_limits(self):
        with self.assertRaises(ValidationError):
            ExecuteApplicationRequest(grant=GRANT, drafted_answers={"Q": " "}, confirm_submit=True)
        with self.assertRaises(ValidationError):
            ExecuteApplicationRequest(grant=GRANT, drafted_answers={"Q": "A"}, vault_credential_labels=["x" * 101], confirm_submit=True)

    def test_search_url_normalizes_bare_domain(self):
        self.assertEqual(tinyfish._search_url("grants.example.org/apply"), "https://grants.example.org/apply")
        self.assertIsNone(tinyfish._search_url("javascript:alert(1)"))


if __name__ == "__main__":
    unittest.main()
