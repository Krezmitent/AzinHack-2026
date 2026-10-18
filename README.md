# AutoGrant

AutoGrant helps founders find funding opportunities, assess their fit, and prepare application drafts. The product combines a Next.js web app with a FastAPI service for grant discovery, scoring, drafting, and application-run tracking.

**Live deployment:** [autogrant-sigma.vercel.app](https://autogrant-sigma.vercel.app) (currently restricted by Vercel team authentication).

AutoGrant is an early-stage prototype. Grant listings and eligibility must be confirmed with each provider. Founders review every draft and remain responsible for submitting applications. A completed automation run is not proof of receipt. No verified founder reviews have been published yet.

![AutoGrant landing page](output/screenshots/autogrant-home.png)

## What the prototype demonstrates

AutoGrant turns a founder profile into a source-linked grant shortlist and editable application drafts. TinyFish Search finds current public pages for a sector and location; TinyFish Fetch retrieves those pages so the service can extract eligibility notes and application links. Gemini scores opportunities against the profile and drafts answers from the founder's supplied information. Every match links to its source, and every draft stays editable before any run can start.

The TinyFish integration is used in two distinct parts of the product:

- **Discovery:** Search returns up to eight public result URLs. Fetch retrieves their HTML, from which AutoGrant extracts page titles, eligibility language, and application links. Results are cached for 10 minutes per location and sector in each service process.
- **Application runs:** After the founder reviews the draft and explicitly starts a run, AutoGrant sends a single asynchronous TinyFish request. Vault access is disabled; the agent is instructed to stop at account or legal-attestation steps. AutoGrant reports “submitted” only with provider confirmation evidence. Ambiguous outcomes stay “unknown.”

This prototype does not claim verified grant coverage, eligibility decisions, application outcomes, or user traction. The sample grant cards and details in the walkthrough video are illustrative.

## Project resources

- [Launch video](brag-output-2026-10-18-174914/brag.mp4) · [WebM](brag-output-2026-10-18-174914/brag.webm) · [video preview](brag-output-2026-10-18-174914/brag.jpg)
- [CI workflow](.github/workflows/ci.yml) · [API service](python-service/app/main.py) · [TinyFish integration](python-service/app/services/tinyfish.py)

![AutoGrant grant board](output/screenshots/autogrant-features.png)

## Product routes

- `/` — product overview and customer review section.
- `/signup` and `/login` — account creation and sign-in with Firebase email/password authentication.
- `/dashboard` — founder profile, grant discovery, match review, answer drafting, and run tracking.
- `/thank-you` — post-action confirmation.
- Unknown routes display a branded 404 page. Each page includes a title and description; social metadata and an Open Graph image are also configured.

Grant actions require a signed-in account with a verified email address. The dashboard also requires the Firebase and provider configuration below.

## Local setup

1. Install Node.js and Python 3.12. From the repository root, run `npm ci`.
2. Copy `.env.example` to `.env.local`. Add the browser configuration from Firebase project settings and the service account JSON used for server-side ID-token verification. Set `NEXT_PUBLIC_SITE_URL` to the site origin; use `http://localhost:3000` for local development. Keep service credentials out of `NEXT_PUBLIC_` variables and out of source control.
3. In Firebase, enable Email/Password authentication, enable email verification, create a Firestore database, and deploy `firestore.rules` before saving profiles. The rules limit profile access to its owner and validate profile data.
4. Copy `python-service/.env.example` to `python-service/.env`. Add the same Firebase service account JSON, a TinyFish API key, and a Gemini API key. The default model is `gemini-2.5-flash`; set `ALLOWED_ORIGINS` to the frontend origin. Keep this file out of source control.
5. Install Python dependencies with `python3.12 -m venv python-service/.venv` and `python-service/.venv/bin/pip install -r python-service/requirements.txt`.
6. Start FastAPI with `cd python-service && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`. In a second terminal, run `npm run dev`. Open `http://localhost:3000`. The service's `/health` endpoint checks process health; `/ready` reports whether required integrations are configured without exposing credentials.

In development, `PYTHON_SERVICE_URL` defaults to `http://localhost:8000`. In production, set it to the private FastAPI service address. Add the site domain to Firebase Authentication's authorized domains. Keep provider keys and service credentials server-side.

## Docker

The frontend and API have separate production images. For a local container run, create `.env.local` and `python-service/.env` as described above, then run:

```sh
docker compose --env-file .env.local up --build
```

Open `http://localhost:3000`. Compose keeps the API on the private container network; the frontend reaches it at `http://api:8000`. The API health check gates frontend startup. Stop the stack with `docker compose down`.

For a server, build and publish the images through GitHub Actions, then use `docker-compose.production.yml`. Set `WEB_IMAGE` and `API_IMAGE` to the desired GHCR tags. Provide `.env.production` and `python-service/.env` on the host with the production environment values and secrets; do not commit either file. `WEB_PORT` controls the host port and defaults to `3000`. Put a TLS reverse proxy and domain in front of the web container, and keep the API port private.

## CI and image delivery

`.github/workflows/ci.yml` runs frontend lint/build and Python service tests for pull requests and pushes to `main`. After both checks pass on `main` or a `v*.*.*` tag, the workflow publishes frontend and API images to GitHub Container Registry (GHCR), tagged with the branch or release, commit SHA, and `latest` on the default branch.

Before the first release, add these non-secret values under **GitHub repository Settings → Secrets and variables → Actions → Variables**. They are embedded in the frontend bundle at build time:

- `NEXT_PUBLIC_FIREBASE_API_KEY`
- `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`
- `NEXT_PUBLIC_FIREBASE_PROJECT_ID`
- `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`
- `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`
- `NEXT_PUBLIC_FIREBASE_APP_ID`
- `NEXT_PUBLIC_SITE_URL`

Firebase web configuration is intended to be public; Firebase authorization and Firestore rules protect user data. Keep `FIREBASE_SERVICE_ACCOUNT_JSON`, `TINYFISH_API_KEY`, and `GEMINI_API_KEY` in runtime secret storage on the deployment host. GHCR packages inherit repository visibility; configure package access before pulling private images from a server.

The workflow publishes versioned, ready-to-run images. Automatic deployment to a live host requires that host's provider and deployment credentials; those are not configured in this repository.

## Request and submission flow

- Each grant API request carries a Firebase ID token. Both the Next.js proxy and FastAPI verify the token and require a verified email. Execution and run-status requests also check token revocation. Firestore access is scoped to the authenticated user's profile.
- Discovery uses a founder's sector and location to search globally with TinyFish Search and Fetch. Results are cached for 10 minutes per sector and location in each Python process. Gemini scores the results, and the founder can review and edit draft answers. Provider eligibility criteria and grant availability should be confirmed at the source.
- Application runs receive the founder-reviewed answers, but no passwords or MFA codes. Vault sign-in is disabled; founders must complete forms that require a provider account directly on that provider's site.
- Starting a run requires explicit confirmation. Before sending the one-time TinyFish `run-async` request, the service records the run under `users/{firebaseUid}/application_runs/{grantHash}`. Repeated requests return the existing record. If the start request times out, the status is `unknown` and requires investigation.
- The dashboard restores recent runs and polls `GET /api/application-runs/{id}` while a run is active. A run is marked submitted only when TinyFish reports `COMPLETED` and returns `submitted: true` with a confirmation number or URL. Other completed, failed, or cancelled runs remain `unknown` unless the result confirms that no submission occurred.

Run tracking follows TinyFish's [async start](https://docs.tinyfish.ai/api-reference/automation/start-automation-asynchronously.md) and [run status](https://docs.tinyfish.ai/api-reference/runs/get-run-by-id.md) APIs. Confirm application receipt in the grant provider's portal.

## Launch video

The 20-second landscape launch video and editable Hyperframes composition are in [`brag-output-2026-10-18-174914/`](brag-output-2026-10-18-174914/). The folder contains an MP4 render ([`brag.mp4`](brag-output-2026-10-18-174914/brag.mp4)), a WebM version ([`brag.webm`](brag-output-2026-10-18-174914/brag.webm)), and a preview image ([`brag.jpg`](brag-output-2026-10-18-174914/brag.jpg)). The storyboard and production brief are also included. Grant names, founder details, scores, and draft text in the video are illustrative examples.

## Verification

Build the frontend with `npm run build`. Run the service tests with `cd python-service && .venv/bin/python -m unittest discover -s tests`. These tests mock external providers and do not verify live Firebase, TinyFish, or Gemini access. Before testing a real application run, use a controlled account and a provider-approved test application. Add reviews to `lib/reviews.ts` only with the reviewer's approval and attribution.

## Data and deployment notes

Profiles are stored in `users/{firebaseUid}` in Firestore. Grant provenance and application runs are stored in server-managed subcollections. Profile text is sent to the scoring and drafting services. Restrict network access to the Python service and store service credentials and provider keys in the deployment secret manager.
