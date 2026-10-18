# AutoGrant

AutoGrant helps founders discover startup grants, understand why an opportunity may fit, prepare editable application answers, and decide whether to begin an external application run. It has a Next.js frontend and a FastAPI provider service. The landing, account, dashboard, and review flows are implemented; live discovery, scoring, drafting, and application runs require Firebase, TinyFish, and Gemini configuration.

This is an early product prototype. Grant availability and eligibility are not guaranteed, generated drafts need founder review, and a provider run does not by itself prove that a grant application was received. The product currently has no published verified founder reviews; the landing page says so instead of showing fabricated testimonials.

## Product routes

- `/` — product landing page, workflow overview, and verified-review empty state.
- `/signup` and `/login` — Firebase email/password account flows. Email verification is required before grant API access.
- `/dashboard` — profile, grant discovery and match review, answer drafting, and application-run tracking.
- `/thank-you` — post-action confirmation page.
- Unknown routes render the branded 404 page. Page-specific titles and descriptions, social metadata, and a generated Open Graph image are included.

Grant actions are available to signed-in, verified users. The dashboard requires the Firebase and backend configuration below; the landing and account pages can still be explored without provider keys.

## Local setup

1. Use Node.js and Python 3.12. Run `npm ci` in this directory.
2. Copy `.env.example` to `.env.local`. Set the browser-safe `NEXT_PUBLIC_FIREBASE_*` values from Firebase project settings and set `FIREBASE_SERVICE_ACCOUNT_JSON` for server-side ID-token verification. Set `NEXT_PUBLIC_SITE_URL` to the public origin (localhost for local development). The service account JSON is a server secret; never give it a `NEXT_PUBLIC_` prefix or commit `.env.local`.
3. In Firebase, enable Email/Password authentication and email verification, create Firestore, and deploy `firestore.rules` before saving profiles. The rules restrict profile reads/writes to their owner and validate profile size and shape.
4. Copy `python-service/.env.example` to `python-service/.env`. Set the **same Firebase service account JSON**, `TINYFISH_API_KEY`, and `GEMINI_API_KEY`. `GEMINI_MODEL` defaults to `gemini-2.5-flash`; set `ALLOWED_ORIGINS` to the frontend origin. Keep this file out of source control.
5. Install Python dependencies with `python3.12 -m venv python-service/.venv` and `python-service/.venv/bin/pip install -r python-service/requirements.txt`.
6. Start FastAPI with `cd python-service && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`. In another terminal, run `npm run dev`. The site is at `http://localhost:3000`; `GET http://localhost:8000/health` checks the Python process and `/ready` reports which required integrations are configured without revealing secrets.

`PYTHON_SERVICE_URL` defaults to `http://localhost:8000` only in development. Set it to the private FastAPI address in production. Configure the Firebase domain as an authorized domain in Firebase Authentication. Do not expose either provider key or the service account through a `NEXT_PUBLIC_` variable.

## Request and submission flow

- Firebase Email/Password provides the browser session. Every grant API request sends a Firebase ID token. The Next.js proxy and FastAPI service both verify it and require a verified email; execution and run-status requests also check token revocation. A supplied `user_id` cannot access another account's Firestore profile.
- Discovery searches for grants in the startup's sector that are open to founders in the location on their profile, then calls TinyFish Search and Fetch. Search results are cached for 10 minutes per sector and location **per Python process**. This is a global search, but search ranking and each provider's eligibility rules still need review. Discovered grant URL pairs are saved to the user's Firestore account; only recently discovered grants can start an application run. Gemini scores results; one score failure does not discard other grants. The founder reviews and edits generated answers.
- The browser agent receives reviewed answers but no passwords or MFA codes. Vault sign-in is disabled until credential ownership can be tied to each user. Forms that require login must be completed by the founder in the grant portal.
- The execution request requires an explicit confirmation flag. It reserves a record under `users/{firebaseUid}/application_runs/{grantHash}` **before** the one-time TinyFish `run-async` POST. Repeat clicks return that record and do not dispatch another run. A start timeout becomes `unknown` and requires manual investigation.
- The dashboard restores recent runs after a reload and polls `GET /api/application-runs/{id}` while they are active. `PENDING` and `RUNNING` are shown as in progress. `COMPLETED` is shown as submitted only when the agent result explicitly says `submitted: true` and contains a confirmation number or URL. A completed run without that evidence, or a failed/cancelled run, is `unknown` unless the result explicitly says it was not submitted.

Run tracking follows TinyFish's [async start](https://docs.tinyfish.ai/api-reference/automation/start-automation-asynchronously.md) and [run status](https://docs.tinyfish.ai/api-reference/runs/get-run-by-id.md) contracts. A provider run marked `COMPLETED` alone does not prove an application was received. Verify each outcome in the grant portal.

## Launch video

The 20-second landscape launch video and its editable Hyperframes composition are in [`brag-output-2026-10-18-174914/`](brag-output-2026-10-18-174914/). The MP4 is [`brag.mp4`](brag-output-2026-10-18-174914/brag.mp4); [`brag.webm`](brag-output-2026-10-18-174914/brag.webm) is an alternate render and [`brag.jpg`](brag-output-2026-10-18-174914/brag.jpg) is a preview still. [`brag-plan.md`](brag-output-2026-10-18-174914/brag-plan.md) and [`composition-brief.md`](brag-output-2026-10-18-174914/composition-brief.md) document the creative direction and render. Grant names, profile details, scores, and answer text shown in the video are fictional illustrative examples, not live offers or product results.

## Verification

Run `npm run build` for the production frontend and `cd python-service && .venv/bin/python -m unittest discover -s tests` for focused service checks. The local tests mock external providers; they do not prove live Firebase, TinyFish, or Gemini behavior. Use a controlled test account and a provider-owned test application before enabling real submissions. Add customer quotes to `lib/reviews.ts` only with attribution and the reviewers' approval.

## Data and deployment notes

Profiles live in `users/{firebaseUid}` in Firestore. Discovered grant provenance and application runs live in server-managed subcollections under that user. The browser sends profile text to the scoring and drafting services. The Python service should be reachable only through a trusted network path where possible, even though it verifies ID tokens itself. Store service account and provider keys in your deployment secret manager.
