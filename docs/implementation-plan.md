# Continuous funding workflow

The implementation extends Next.js, FastAPI and Firestore. TinyFish supplies web evidence and browser actions; Gemini remains the writing and assessment engine because TinyFish does not document a drop-in general text generation API.

## PR sequence

1. Saved funding workspace: persist opportunities and versioned drafts; separate eligibility checks from strategic fit; retain evidence freshness and founder facts.
2. TinyFish inspection: asynchronously inspect actual forms and programme details, extract structured requirements, show live progress, and draft against those requirements.
3. Funding watches and application tracking: public Page/Topic monitors, durable webhook processing, meaningful change alerts, reminders, and a separate application lifecycle.

Each slice must pass the frontend lint/build and Python service tests. Retain owner isolation, explicit submission consent, and no blind retries for consequential starts. Use stacked PRs where consumers depend on foundation changes. Do not merge without a separate instruction.

## Operational design

Store provider run IDs and durable work before returning to the browser. Webhooks enter a deduplicated inbox; a scheduled worker processes pending work and reconciles status. No workflow depends on an open browser tab. Public monitors use TinyFish's schedule; private portal checks require an application scheduler and an explicitly user-owned Browser Context Profile.

Application decisions and automation outcomes are separate. A failed check never overwrites the last known application status. Preserve edited drafts when sources change; mark them as requiring review. Keep saved browser profiles and credential identifiers behind server ownership checks. A live preview is read-only, not a human takeover UI.

## Deferred stretch work

Research briefs and authenticated portal connectors are optional follow-ups. Enable portal automation only after testing a supported provider and a user-specific session setup. Keep Vault disabled with the current shared service key. Capture artifacts and Research access depend on TinyFish account capabilities.
