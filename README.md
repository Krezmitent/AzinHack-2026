# AutoGrant AI

Autonomous grant discovery, matching, drafting, and application-run orchestration for hackathon demos.

## Project layout

```text
autogrant-ai/
├── app/                         # Next.js App Router UI and API proxy routes
├── lib/                         # Firebase client and frontend API helpers
├── python-service/
│   ├── app/                     # FastAPI and AI/automation services
│   └── requirements.txt
├── firestore.rules               # Firestore schema access rules
├── .env.example                  # Required configuration keys
└── next.config.mjs
```

## Run locally

1. Copy `.env.example` to `.env.local`, then supply Firebase browser configuration and Python-only API keys.
2. In one terminal: `npm install && npm run dev`.
3. In another: `cd python-service && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000`.
4. Deploy `firestore.rules` with the Firebase CLI. Enable anonymous sign-in in Firebase Authentication for the demo dashboard.

The execute endpoint is deliberately protected by a `confirm_submit: true` request field. Vault labels are passed to TinyFish; passwords and MFA secrets must never be sent to this application or to Gemini.

## Firestore document schema

```text
users/{firebaseUid}
  sector: string
  revenue: string
  demographics: string
  pitchDeckText: string
  updatedAt: ISO-8601 string

grants/{grantId}                # created by a trusted backend service account
  title: string
  source_url: string
  application_url: string | null
  eligibility_criteria: string[]
  clean_markdown: string
  match_score: number | null
  match_reason: string | null
```

For a production implementation, protect the Next.js API routes with Firebase ID-token verification and add an application audit collection before enabling autonomous execution.
