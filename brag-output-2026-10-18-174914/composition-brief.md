# Hyperframes Composition Brief: AutoGrant

## Objective
Create a 20-second polished launch video for AutoGrant that shows the real founder workflow and keeps the founder’s decision-making visible.

## Output
- Composition directory: `brag-output-2026-10-18-174914/composition/`
- Rendered video: `brag-output-2026-10-18-174914/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 20 seconds

## Source Material
- Project root: `/home/arachknight/Documents/Projects/Hackathon/AzinHack-2026`
- Primary files read: `app/page.tsx`, `app/globals.css`, `app/dashboard/Dashboard.tsx`, `README.md`, `package.json`
- Product name: AutoGrant
- Tagline / strongest claim: “A better way to find your next grant.”
- Key UI or visual moment: the dashboard profile beside grant cards, then the editable “Review your draft” panel with the “Your call” badge.
- Copy that must appear verbatim: “A better way to find your next grant.” / “Review your draft” / “Your call” / “Scan for grants” / “Start application run”
- Product facts: grant search uses TinyFish; grant scoring and answer drafts use Gemini; drafts are editable; application runs require explicit user confirmation. Do not imply eligibility is guaranteed or a provider submission succeeded.
- Demo data: use fictional, generic examples only. Keep “Illustrative demo data” visible anywhere demo profiles/scores appear.

## Creative Direction
- Tone preset: polished
- Creative direction: premium, lively product launch with founder-focused clarity
- Interpretation: clean, real product UI with brisk, purposeful motion and a restrained musical bed.
- Angle: move from messy grant research into a focused desk: profile → explainable shortlist → founder-reviewed draft.
- Hook: “Finding funding shouldn’t start with a spreadsheet.”
- Outro / punchline: AutoGrant / “A better way to find your next grant.” / “Build your shortlist.”
- Avoid generic SaaS copy, fabricated traction or outcomes, abstract filler, real user data, and any visual implication that the app submitted an application.

## Visual Identity
- Background: `#f7f8fc`
- Text: `#1e2443`
- Accent: `#4945e6`, with secondary lilac `#e9e7ff` and mint `#c9f2dd`
- Display font: Syne
- Body font: Manrope
- Visual references: actual dashboard panel and card structure from `app/dashboard/Dashboard.tsx`; brand spacing and wordmark from `app/globals.css` and `components/SiteHeader.tsx`.

## Storyboard
Use `brag-plan.md` as the creative contract.
1. Less spreadsheet — 3s — grid resolves into the AutoGrant funding desk.
2. Start with your story — 4s — actual profile fields fill; scan is clicked.
3. A shortlist with reasons — 5s — two labeled illustrative grant cards arrive sequentially.
4. Draft. Review. Decide. — 5s — editable draft and idle run button; emphasize “Your call”.
5. Brand close — 3s — wordmark, core promise, shortlist CTA.

## Audio
- Audio role: polished rhythmic support.
- Audio arc: pickup, shortlist lift, softer founder-control moment, logo resolution.
- Music: `assets/music/happy-beats-business-moves-vol-10-by-ende-dot-app.mp3`
- Music treatment: 0.30–0.35 level; gentle fade during final second.
- Music cue guidance: use the bundled preset `assets/music/cues/happy-beats-business-moves-vol-10-by-ende-dot-app.music-cues.json` (109.96 BPM); align profile fields to 3.55s, 4.10s, 4.64s; grant cards to 7.79s and 8.22s; draft reveal to 12.56s; and final CTA to 18.01s. The subtle glow follows the extracted 0.3s music envelope.
- Audio-reactive treatment: subtle radial glow follows a downsampled music envelope extracted with the HyperFrames audio CLI; no waveform/equalizer.
- Audio-coupled moments: scan click, two sequential card arrivals, brand lockup.
- SFX selection guidance: soft UI click and restrained card/drop or success tone, no submission sound.
- SFX analysis guidance: `/home/arachknight/.codex/skills/brag/assets/sfx/sfx-analysis.md`.
- Exact SFX choice: choose after motion exists and copy selected clips into `composition/assets/`.
- Audio files: chosen music already copied into `composition/assets/music/`.

## Hyperframes Instructions
Use the installed Hyperframes authoring skills and current composition conventions. Build locally, inspect the output, run `npx hyperframes check` inside the composition, and render locally. Show actual AutoGrant UI structure in at least two scenes. Keep all sample data labeled illustrative and keep the application-run action idle.
