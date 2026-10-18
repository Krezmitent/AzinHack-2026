# Brag Plan: AutoGrant

## What is this app?
AutoGrant helps founders discover startup grants, understand why each may fit, prepare draft answers, and decide whether to begin an application run.

## The angle
A grant hunt turns into a clearer funding desk: the founder’s story becomes a tailored shortlist, then an editable draft. The product feels useful because the person stays in control at every consequential step.

## Hook (first 2–3 seconds)
A dense spreadsheet grid snaps into one clean question: “Finding funding shouldn’t start with a spreadsheet.” The first 2 seconds should make the pain recognizable, then reveal the AutoGrant mark.

## Key moments (the middle)
- A demo founder profile fills in: Climate tech · India · Pre-revenue.
- A scan resolves into a concise shortlist with match scores and eligibility notes.
- A grant answer draft opens in an editable review panel marked “Your call.”

## Outro / punchline
AutoGrant. “Find your next right fit.” Button-like prompt: “Build your shortlist.” No claim that a grant was submitted or awarded.

## User flow worth showing
Profile → scan and score sourced grant opportunities → draft answers → human review before any application run.

## Tone
- Preset: polished
- Creative direction: premium, lively product launch with the pace of a founder-facing startup trailer
- Interpretation: precise UI moves, confident typography, high-contrast indigo accents, and a warm rhythmic bed; keep the product and human review legible.

## Format: landscape — 1920x1080
## Duration: 20 seconds

## Visual identity (from the project)
- Background: `#f7f8fc`
- Accent: `#4945e6` (secondary lilac `#e9e7ff`, mint `#c9f2dd`)
- Text: `#1e2443`
- Display font: Syne
- Body font: Manrope
- Strongest visual element: the working funding desk: startup profile beside a grant board, then the “Review your draft / Your call” panel.

## Share copy (draft)
A better grant search starts with your story: AutoGrant helps founders find a shortlist, understand the fit, and shape the first draft—with the final call still theirs.

## Audio direction
- Role: bright, polished rhythmic bed with a few restrained UI accents
- Music: `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3` (compact, punchy)
- Music treatment: start immediately at 0.30–0.35 volume; build into the UI reveal; gently fade during the final second.
- Music cue guidance: bundled cue preset at `composition/assets/music/cues/happy-beats-business-moves-vol-10-by-ende-dot-app.music-cues.json` (109.96 BPM). Strong cues at 3.55s, 6.28s, 11.46s, 15.82s, and 18.01s; use only where they support readability. The final CTA lands on the 18.01s cue; profile fields and cards use the beat grid. Do not compromise reading time.
- Audio-reactive treatment: a subtle radial glow follows the extracted music envelope, no waveform graphics.
- SFX posture: sparse; soft click for scan, light card arrival for shortlist, gentle confirmation tone for the draft review.
- Audio-coupled moments: the scan button press, sequential grant-card entrances, and final wordmark landing.
- Restraint rule: never make a draft look like a successful application submission.

## Storyboard

### Scene 1 — Less spreadsheet — 3s
A real-looking spreadsheet grid crowds a pale canvas. It folds into a clean AutoGrant funding desk. Copy: “Finding funding shouldn’t start with a spreadsheet.” Wordmark snaps in at the end. No fabricated metrics.
Sequential/interaction: spreadsheet rows collapse into one product frame.
Audio intent: immediate rhythmic pickup; small, clean transition accent.
Audio-coupled idea: grid resolves on a strong music moment.
Music: bright, restrained business-pop bed.
Transition mood: clean wipe → Scene 2

### Scene 2 — Start with your story — 4s
Recreate the actual profile panel from `app/dashboard/Dashboard.tsx`: Sector, Location, Revenue / stage, startup overview. Enter generic demo values: “Climate tech”, “India”, “Pre-revenue”. A scan button is pressed. Small visible label: “Illustrative demo data”.
Sequential/interaction: fields fill one by one; cursor clicks “Scan for grants”.
Audio intent: focused, forward movement.
Audio-coupled idea: quiet typing ticks on two field arrivals and one click at scan.
Music: bed continues.
Transition mood: brisk product wipe → Scene 3

### Scene 3 — A shortlist with reasons — 5s
The real grant-card design appears beside the profile panel. Two clearly illustrative sample cards arrive in sequence: “Sample climate fund” at “88% Match”; “Sample founder grant” at “74% Match”. Show eligibility notes and source-link treatment. Keep “Illustrative demo data” visible so scores cannot be mistaken for live grants.
Sequential/interaction: cards enter one at a time; scores count up modestly and stop. Use two readable holds.
Audio intent: satisfying discovery reveal, not a victory claim.
Audio-coupled idea: first and second card arrival can align to separated beats; hold both after reveal.
Music: bed lifts slightly.
Transition mood: soft crossfade → Scene 4

### Scene 4 — Draft. Review. Decide. — 5s
Show the actual “Review your draft” panel from the dashboard. A sample answer appears in an editable field. Highlight the existing “Your call” badge and “Start application run” button, but do not click it. Copy: “Every answer stays yours to review.”
Sequential/interaction: sample text types in; a caret moves once to imply editing; button remains idle.
Audio intent: warmer and more deliberate; one soft accent on the review badge.
Audio-coupled idea: a soft review accent lands on the badge; no typing sound and no submission sound.
Music: pull back slightly under the human-control message.
Transition mood: confident crossfade → Scene 5

### Scene 5 — Brand close — 3s
AutoGrant wordmark and its exact core benefit: “A better way to find your next grant.” Then CTA-style line: “Build your shortlist.” Preserve generous negative space and one indigo accent.
Sequential/interaction: wordmark lands, then the promise, headline, and CTA enter in sequence; hold the CTA through the final frame.
Audio intent: clean resolution.
Audio-coupled idea: wordmark locks to a strong beat; fade bed out over the final second.
Music: warm exit.
Transition mood: fade to brand close.

**Music mood for this video:** upbeat, polished
**Audio summary:** rhythmic lift into the shortlist reveal, a slight softening for founder review, and one clear final brand landing.

## Accuracy and privacy notes
All visible grant names, profile details, scores, and answer text are fictional examples created only for this video and must be labeled as illustrative. Never show an actual account, email, API key, grant provider submission, award, or success confirmation. Keep the application-run button idle.
