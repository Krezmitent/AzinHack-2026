"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { onAuthStateChanged, signOut } from "firebase/auth";
import { doc, getDoc, setDoc } from "firebase/firestore";
import { firebaseServices } from "@/lib/firebase";
import { discoverGrants, draftApplication, executeApplication, getApplicationRun, listApplicationRuns, scoreGrant, loadWorkspace, saveDraft, startInspection, getInspection } from "@/lib/api";
import type { ApplicationRun } from "@/lib/api";
import type { Grant, InspectionRun, SavedDraft, StartupProfile } from "@/lib/types";
import { draftIssues, formQuestions, submissionAnswers } from "@/lib/application";

const initialProfile: StartupProfile = { sector: "", location: "", revenue: "", demographics: "", pitchDeckText: "", companyFacts: "" };
const MAX_PITCH_LENGTH = 100_000;
const MAX_PITCH_FILE_BYTES = 100_000;
const SCORE_CONCURRENCY = 3;
type Notice = { message: string; tone: "info" | "success" | "error" };
type ApplicationReview = { grant: Grant; answers: Record<string, string>; revision: number; source_version: string; profile: StartupProfile };

function sameProfile(a: StartupProfile, b: StartupProfile) {
  return (Object.keys(initialProfile) as (keyof StartupProfile)[]).every((key) => (a[key] || "") === (b[key] || ""));
}

export default function Dashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<StartupProfile>(initialProfile);
  const [grants, setGrants] = useState<Grant[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<Notice>({ message: "Start with your startup details. We’ll use them to find and rank grants.", tone: "info" });
  const [uid, setUid] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [inspections, setInspections] = useState<InspectionRun[]>([]);
  const [savedDrafts, setSavedDrafts] = useState<SavedDraft[]>([]);
  const [review, setReview] = useState<ApplicationReview | null>(null);
  const [runResult, setRunResult] = useState<ApplicationRun | null>(null);
  const [recentRuns, setRecentRuns] = useState<ApplicationRun[]>([]);
  const [runUncertain, setRunUncertain] = useState(false);
  const loggingOut = useRef(false);

  useEffect(() => {
    let active = true;
    try {
      const { auth, db } = firebaseServices();
      const unsubscribe = onAuthStateChanged(auth, async (user) => {
        if (!active) return;
        if (!user) {
          setUid(null);
          setGrants([]);
          setReview(null);
          setSavedDrafts([]);
          setInspections([]);
          setRecentRuns([]);
          setAuthReady(true);
          if (!loggingOut.current) router.replace("/login");
          return;
        }
        setAuthReady(false);
        setUid(user.uid);
        setProfile(initialProfile);
        if (!user.emailVerified) {
          setUid(null);
          setAuthReady(true);
          setNotice({ message: "Verify your email address, then log in before using grant tools.", tone: "error" });
          router.replace("/login");
          return;
        }
        void listApplicationRuns().then(({ runs }) => {
          if (active && auth.currentUser?.uid === user.uid) setRecentRuns(runs);
        }).catch(() => {
          if (active && auth.currentUser?.uid === user.uid) setNotice({ message: "Could not load recent application runs. Check the grant portal before starting another run.", tone: "error" });
        });
        try {
          const [saved, workspace] = await Promise.all([getDoc(doc(db, "users", user.uid)), loadWorkspace()]);
          if (active && auth.currentUser?.uid === user.uid) {
            setGrants(workspace.opportunities);
            setSavedDrafts(workspace.drafts);
            setInspections(workspace.inspections);
          }
          if (active && auth.currentUser?.uid === user.uid && saved.exists()) {
            const data = saved.data();
            setProfile({
              sector: typeof data.sector === "string" ? data.sector : "",
              location: typeof data.location === "string" ? data.location : "",
              revenue: typeof data.revenue === "string" ? data.revenue : "",
              demographics: typeof data.demographics === "string" ? data.demographics : "",
              pitchDeckText: typeof data.pitchDeckText === "string" ? data.pitchDeckText : "",
              companyFacts: typeof data.companyFacts === "string" ? data.companyFacts : ""
            });
            setNotice({ message: "Your saved profile is ready. Scan for grants when you are.", tone: "success" });
          }
        } catch (error) {
          if (active && auth.currentUser?.uid === user.uid) setNotice({ message: error instanceof Error ? error.message : "Could not load your saved profile.", tone: "error" });
        } finally {
          if (active && auth.currentUser?.uid === user.uid) setAuthReady(true);
        }
      });
      return () => { active = false; unsubscribe(); };
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Firebase is unavailable.", tone: "error" });
      setAuthReady(true);
    }
  }, [router]);

  useEffect(() => {
    if (!uid || !recentRuns.some((run) => run.status === "starting" || run.status === "pending")) return;
    const timer = window.setInterval(() => {
      for (const item of recentRuns.filter((run) => run.status === "starting" || run.status === "pending").slice(0, 3)) {
        void getApplicationRun(item.id).then(({ run }) => {
          setRecentRuns((current) => current.map((existing) => existing.id === run.id ? run : existing));
          setRunResult((current) => current?.id === run.id ? run : current);
        }).catch(() => {
          // A transient status error is not evidence of a failed or successful submission.
        });
      }
    }, 8_000);
    return () => window.clearInterval(timer);
  }, [uid, recentRuns]);

  function rememberRun(run: ApplicationRun) {
    setRecentRuns((current) => [run, ...current.filter((item) => item.id !== run.id)].slice(0, 20));
    setRunResult(run);
  }

  const highScoreCount = useMemo(() => grants.filter((grant) => (grant.match_score ?? 0) >= 70).length, [grants]);
  const profileReady = profile.sector.trim().length > 0 && profile.location.trim().length > 0 && profile.revenue.trim().length > 0 && profile.pitchDeckText.trim().length >= 20;
  const canDiscover = Boolean(uid) && authReady && profileReady;
  const profileDisabled = Boolean(busy) || !authReady;
  const reviewStale = review && (review.source_version !== review.grant.source_version || !sameProfile(review.profile, profile));
  const reviewProblems = review ? draftIssues(review.grant, review.answers) : [];
  const reviewNeedsWork = reviewProblems.length > 0;

  function update(field: keyof StartupProfile, value: string) {
    setProfile((current) => ({ ...current, [field]: value }));
    if (grants.length || review) {
      setGrants((current) => current.map((grant) => ({ ...grant, match_score: undefined, match_reason: undefined, eligibility_checks: [] })));
      setRunResult(null);
      setNotice({ message: "Your profile changed. Scan again to refresh fit assessments. Saved drafts need another review.", tone: "info" });
    }
  }

  async function uploadPitchDeck(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    event.target.value = "";
    if (!file.name.toLowerCase().endsWith(".txt")) {
      setNotice({ message: "Choose a plain-text (.txt) pitch deck.", tone: "error" });
      return;
    }
    if (file.size > MAX_PITCH_FILE_BYTES) {
      setNotice({ message: "This pitch deck is too large. Upload a .txt file under 100 KB or paste a shorter overview.", tone: "error" });
      return;
    }
    try {
      const content = await file.text();
      if (content.length > MAX_PITCH_LENGTH) throw new Error("The pitch deck exceeds 100,000 characters.");
      update("pitchDeckText", content);
      setNotice({ message: `Added ${file.name} to your startup profile.`, tone: "success" });
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Could not read that file.", tone: "error" });
    }
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || !authReady) return;
    if (!profile.sector.trim() || !profile.location.trim() || !profile.revenue.trim() || profile.pitchDeckText.trim().length < 20) {
      setNotice({ message: "Add your sector, location, stage, and at least 20 characters about your startup before saving.", tone: "error" });
      return;
    }
    if (!uid) {
      setNotice({ message: "Sign in to save your profile. If sign-in is unavailable, check the Firebase configuration.", tone: "error" });
      return;
    }
    setBusy("save");
    try {
      const { db } = firebaseServices();
      await setDoc(doc(db, "users", uid), {
        sector: profile.sector.trim(), location: profile.location.trim(), revenue: profile.revenue.trim(),
        demographics: profile.demographics.trim(), pitchDeckText: profile.pitchDeckText.trim(), companyFacts: (profile.companyFacts || "").trim(),
        updatedAt: new Date().toISOString()
      }, { merge: true });
      setNotice({ message: "Profile saved. You’re ready to scan for grants.", tone: "success" });
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Could not save your profile.", tone: "error" });
    } finally { setBusy(null); }
  }

  async function findGrants() {
    if (busy || !canDiscover) return;
    setBusy("discover");
    setReview(null);
    setRunResult(null);
    setGrants([]);
    try {
      const discovered = await discoverGrants(profile.location.trim(), profile.sector.trim());
      if (!Array.isArray(discovered.grants)) throw new Error("The grant service returned an invalid shortlist.");
      setNotice({ message: `Found ${discovered.grants.length} opportunities. Checking each match…`, tone: "info" });
      const results: Grant[] = new Array(discovered.grants.length);
      let next = 0;
      let failed = 0;
      let firstError = "";
      const scoreNext = async () => {
        while (next < discovered.grants.length) {
          const index = next++;
          const grant = discovered.grants[index];
          try {
            results[index] = { ...grant, ...(await scoreGrant(grant, profile)) };
          } catch (error) {
            failed += 1;
            if (!firstError) firstError = error instanceof Error ? error.message : "Scoring failed.";
            results[index] = { ...grant, match_score: undefined, match_reason: undefined };
          }
        }
      };
      await Promise.all(Array.from({ length: Math.min(SCORE_CONCURRENCY, results.length) }, () => scoreNext()));
      const scored = results.sort((a, b) => (b.match_score ?? -1) - (a.match_score ?? -1));
      setGrants(scored);
      if (!scored.length) setNotice({ message: "No grants came back from this scan. Try again later.", tone: "info" });
      else if (failed) setNotice({ message: `Found ${scored.length} opportunities, but ${failed} could not be scored. You can still view their sources. ${firstError}`, tone: "error" });
      else setNotice({ message: `Found and ranked ${scored.length} grant opportunities.`, tone: "success" });
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Could not discover grants.", tone: "error" });
    } finally { setBusy(null); }
  }

  useEffect(() => {
    if (!uid || !inspections.some((run) => ["starting", "pending"].includes(run.status))) return;
    let active = true;
    const timer = window.setInterval(() => {
      for (const item of inspections.filter((run) => ["starting", "pending"].includes(run.status)).slice(0, 3)) {
        void getInspection(item.id).then(({ inspection, grant }) => {
          if (!active) return;
          setInspections((current) => current.map((run) => run.id === item.id ? inspection : run));
          if (inspection.status === "completed") {
            setGrants((current) => current.map((value) => value.id === grant.id ? grant : value));
            setReview((current) => {
              if (!current || current.grant.id !== grant.id) return current;
              const answers = grant.inspection?.complete ? Object.fromEntries(formQuestions(grant).map((question) =>
                [question.label, current.answers[question.label] || "Information not provided; complete this new form question."])) : current.answers;
              return { ...current, grant, answers };
            });
          }
        }).catch(() => { /* Durable worker reconciliation continues after transient poll failures. */ });
      }
    }, 8000);
    return () => { active = false; window.clearInterval(timer); };
  }, [uid, inspections]);

  async function inspectForm(grant: Grant) {
    if (busy) return;
    setBusy(`inspect:${grant.id}`);
    try {
      const { inspection } = await startInspection(grant);
      setInspections((current) => [...current.filter((item) => item.id !== grant.id), inspection]);
      setNotice({ message: inspection.message || "Read-only inspection started.", tone: "info" });
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Could not inspect the application.", tone: "error" });
    } finally { setBusy(null); }
  }

  async function refreshFit(grant: Grant) {
    if (busy || !profileReady) return;
    setBusy(`score:${grant.id}`);
    try {
      const assessment = await scoreGrant(grant, profile);
      setGrants((current) => current.map((item) => item.id === grant.id ? { ...item, ...assessment } : item));
      setNotice({ message: "Fit and eligibility checks updated using the current requirements.", tone: "success" });
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Could not refresh fit.", tone: "error" });
    } finally { setBusy(null); }
  }

  async function prepareDraft(grant: Grant) {
    if (busy) return;
    setBusy(`draft:${grant.source_url}`);
    try {
      const existing = savedDrafts.find((draft) => draft.opportunity_id === grant.id);
      if (existing) {
        const questions = formQuestions(grant);
        const answers = questions.length ? Object.fromEntries(questions.map((question) => [question.label, existing.answers[question.label] || "Information not provided; complete this new form question."])) : existing.answers;
        setReview({ grant, ...existing, answers });
      } else {
        const questions = formQuestions(grant).map((question) => question.label);
        if (!grant.inspection?.complete || !questions.length) throw new Error("Inspect the complete form before drafting answers.");
        const { answers } = await draftApplication(grant, profile, questions);
        const { draft } = await saveDraft(grant, profile, answers, 0);
        setSavedDrafts((current) => [...current, draft]);
        setReview({ grant, ...draft });
      }
      setRunResult(null);
      setRunUncertain(false);
      setNotice({ message: `Draft ready for ${grant.title}. Review and edit the answers before starting an application run.`, tone: "info" });
      window.setTimeout(() => document.getElementById("application-review")?.scrollIntoView({ behavior: "smooth", block: "nearest" }), 0);
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Could not draft this application.", tone: "error" });
    } finally { setBusy(null); }
  }

  async function persistDraft() {
    if (!review || busy || reviewStale) return;
    setBusy("save-draft");
    try {
      const { draft } = await saveDraft(review.grant, profile, review.answers, review.revision);
      setSavedDrafts((current) => [...current.filter((item) => item.opportunity_id !== draft.opportunity_id), draft]);
      setReview({ grant: review.grant, ...draft });
      setNotice({ message: `Draft revision ${draft.revision} saved.`, tone: "success" });
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "Could not save draft.", tone: "error" });
    } finally { setBusy(null); }
  }

  async function startApplication() {
    if (!review || reviewNeedsWork || reviewStale || busy || runUncertain) return;
    const grant = review.grant;
    const existing = recentRuns.find((run) => run.source_url === grant.source_url && run.application_url === (grant.application_url || grant.source_url));
    if (existing) {
      setRunResult(existing);
      setNotice({ message: "An application run already exists for this grant. Check its status below before taking further action.", tone: "info" });
      return;
    }
    setBusy(`execute:${grant.source_url}`);
    setRunResult(null);
    let dispatched = false;
    try {
      const { draft } = await saveDraft(grant, profile, review.answers, review.revision);
      setSavedDrafts((current) => [...current.filter((item) => item.opportunity_id !== grant.id), draft]);
      setReview({ grant, ...draft });
      dispatched = true;
      const { run } = await executeApplication(grant, submissionAnswers(draft.answers), [], draft.revision);
      if (!run?.id || !["starting", "pending", "submitted", "not_submitted", "unknown"].includes(run.status)) throw new Error("The run service returned no reliable status.");
      rememberRun(run);
      setNotice({ message: run.message, tone: run.status === "not_submitted" || run.status === "unknown" ? "error" : run.status === "submitted" ? "success" : "info" });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not determine the application run status.";
      if (!dispatched) {
        setNotice({ message, tone: "error" });
        return;
      }
      setRunUncertain(true);
      try {
        const { runs } = await listApplicationRuns();
        setRecentRuns(runs);
        const recovered = runs.find((run) => run.source_url === grant.source_url && run.application_url === (grant.application_url || grant.source_url));
        if (recovered) setRunResult(recovered);
      } catch { /* Keep retries disabled until the saved status can be checked. */ }
      setNotice({ message: `${message} Check recent runs and the grant portal before another attempt.`, tone: "error" });
    } finally { setBusy(null); }
  }

  async function logOut() {
    loggingOut.current = true;
    try {
      await signOut(firebaseServices().auth);
      router.replace("/");
    } catch (error) {
      loggingOut.current = false;
      setNotice({ message: error instanceof Error ? error.message : "Could not log out.", tone: "error" });
    }
  }

  return (
    <div className="app-shell" id="top">
      <header className="topbar page-wrap">
        <Link className="brand" href="/" aria-label="AutoGrant home"><span className="brand-mark" aria-hidden="true"><span /><span /><span /><span /></span><span>AutoGrant<span className="brand-period">.</span></span></Link>
        <nav className="top-nav" aria-label="Dashboard navigation"><Link href="/">Home</Link><a href="#profile">Your profile</a><a href="#matches">Grant board</a></nav>
        <div className="topbar-actions"><span className={`connection-status ${uid && authReady ? "is-connected" : ""}`}><span />{!authReady ? "Loading profile" : uid ? "Profile connected" : "Sign in needed"}</span>{uid ? <button type="button" className="topbar-logout" onClick={logOut} disabled={Boolean(busy)}>Log out</button> : <Link className="topbar-logout" href="/login">Log in</Link>}</div>
      </header>

      <main>
        <div className="page-wrap workspace">
          <div className="workspace-heading"><div><h1>Your funding desk</h1><p>One place to shape your story and see what fits.</p></div><span className="workspace-note">A better shortlist starts with your story.</span></div>
          <div className={`notice notice-${notice.tone}`} role="status" aria-live="polite"><span className="notice-icon" aria-hidden="true">{notice.tone === "success" ? "✓" : notice.tone === "error" ? "!" : "✳"}</span><span>{notice.message}</span></div>
          <div className="workspace-grid">
            <section className="profile-panel" id="profile" aria-labelledby="profile-heading">
              <div className="profile-heading"><div className="panel-symbol" aria-hidden="true">✳</div><div><h3 id="profile-heading">Your startup</h3><p>Give us the details that matter for eligibility.</p></div></div>
              <form onSubmit={saveProfile} className="profile-form">
                <div className="field"><label htmlFor="sector">What space are you in?</label><input id="sector" required maxLength={120} disabled={profileDisabled} value={profile.sector} onChange={(event) => update("sector", event.target.value)} placeholder="Climate tech, health, fintech…" /></div>
                <div className="field"><label htmlFor="location">Where is your startup based?</label><input id="location" required maxLength={120} disabled={profileDisabled} value={profile.location} onChange={(event) => update("location", event.target.value)} placeholder="India, Germany, Brazil…" /><span className="field-help">We search worldwide for grants open to founders in this location.</span></div>
                <div className="field"><label htmlFor="revenue">What stage are you at?</label><input id="revenue" required maxLength={120} disabled={profileDisabled} value={profile.revenue} onChange={(event) => update("revenue", event.target.value)} placeholder="Pre-revenue, $120k ARR…" /></div>
                <div className="field"><label htmlFor="demographics">Founder details <span className="optional">Optional</span></label><textarea id="demographics" rows={3} maxLength={2000} disabled={profileDisabled} value={profile.demographics} onChange={(event) => update("demographics", event.target.value)} placeholder="Share details relevant to grant eligibility." /></div>
                <div className="field"><label htmlFor="company-facts">Company eligibility facts <span className="optional">Optional</span></label><textarea id="company-facts" maxLength={4000} rows={3} disabled={profileDisabled} value={profile.companyFacts || ""} onChange={(event) => update("companyFacts", event.target.value)} placeholder="Legal entity, incorporation date and country, team size, previous funding…" /><span className="field-help">Unknown facts remain unknown in eligibility checks.</span></div>
                <div className="field"><label htmlFor="pitch">Tell us what you’re building</label><textarea id="pitch" required minLength={20} maxLength={MAX_PITCH_LENGTH} rows={7} disabled={profileDisabled} value={profile.pitchDeckText} onChange={(event) => update("pitchDeckText", event.target.value)} placeholder="Paste your plain-text pitch deck or write a short overview of your startup." /><span className="field-help">At least 20 characters. A few clear paragraphs work best.</span></div>
                <input id="pitch-file" className="visually-hidden file-input" type="file" accept=".txt,text/plain" disabled={profileDisabled} onChange={uploadPitchDeck} /><label className="upload-control" htmlFor="pitch-file"><span aria-hidden="true">＋</span> Upload a .txt pitch deck</label>
                <button className="save-button" type="submit" disabled={profileDisabled}>{busy === "save" ? "Saving profile…" : "Save profile"}<span aria-hidden="true">↗</span></button>
                <p className="form-footnote">Saving stores your profile in Firestore. Scanning and drafting send relevant profile and grant details to our AI services.</p>
              </form>
            </section>

            <section className="matches-panel" id="matches" aria-labelledby="matches-heading">
              <div className="matches-heading"><div><h3 id="matches-heading">Grant board</h3><p>Opportunities for your startup, with scores when available.</p></div><button className="discover-button" type="button" onClick={findGrants} disabled={Boolean(busy) || !canDiscover}><span className="button-search" aria-hidden="true">⌕</span>{busy === "discover" ? "Scanning…" : "Scan for grants"}</button></div>
              {authReady && !uid && <p className="discover-hint">Sign in to scan for grants and save your progress.</p>}
              {authReady && uid && !profileReady && <p className="discover-hint">Add your sector, location, stage, and a short startup overview to unlock the scan.</p>}
              {grants.length > 0 ? <><div className="results-summary"><span>{grants.length} {grants.length === 1 ? "opportunity" : "opportunities"} found</span><span>{highScoreCount} strong {highScoreCount === 1 ? "match" : "matches"}</span></div><div className="grant-list">{grants.map((grant) => {
                const isReviewing = review?.grant.source_url === grant.source_url;
                const drafting = busy === `draft:${grant.source_url}`;
                const executing = busy === `execute:${grant.source_url}`;
                const existingRun = recentRuns.find((run) => run.source_url === grant.source_url && run.application_url === (grant.application_url || grant.source_url));
                const inspectionRun = inspections.find((item) => item.id === grant.id);
                const inspecting = inspectionRun && ["starting", "pending"].includes(inspectionRun.status);
                return <article className="grant-card" key={grant.source_url}>
                  <div className="grant-main"><div className="grant-score"><strong>{grant.match_score == null ? "—" : <>{grant.match_score}<span>/100</span></>}</strong><small>{grant.match_score == null ? "Unscored" : "Fit"}</small></div><div className="grant-copy"><h4>{grant.title}</h4><p>{grant.match_reason || (grant.match_score == null ? "Scoring is unavailable. Check eligibility at the source." : "Check the source for eligibility details.")}</p></div></div>
                  <div className="grant-criteria"><span>Eligibility notes</span><p>{grant.eligibility_criteria.slice(0, 3).join(" / ") || "Review the source page for criteria."}</p></div>
                  {grant.checked_at && <p className="field-help">Source retrieved {new Date(grant.checked_at).toLocaleString()}. Fit is not a funding probability.</p>}
                  {!!grant.eligibility_checks?.length && <details className="grant-criteria"><summary>Eligibility checklist</summary>{grant.eligibility_checks.map((check, index) => <p key={index}><strong>{check.status}: {check.criterion}</strong><br />{check.reason}</p>)}</details>}
                  {grant.inspection && <div className="grant-criteria"><p><strong>{grant.inspection.provider || "Provider unconfirmed"}</strong>{grant.inspection.round_name ? ` · ${grant.inspection.round_name}` : ""}</p><p>{[grant.inspection.amount, grant.inspection.deadline_date ? `Deadline date: ${grant.inspection.deadline_date}` : ""].filter(Boolean).join(" · ")}</p><p>{grant.inspection.explanation}</p>{grant.inspection.required_documents.length > 0 && <p>Required documents: {grant.inspection.required_documents.join(", ")}</p>}<details><summary>Source evidence</summary>{grant.inspection.evidence.map((fact, index) => <p key={index}><strong>{fact.field}: {fact.value}</strong><br />“{fact.quote}” <a href={fact.source_url} target="_blank" rel="noreferrer">Source</a></p>)}</details></div>}
                  {inspectionRun && <p className="field-help" role="status">{inspectionRun.message || inspectionRun.status}</p>}
                  {inspecting && inspectionRun.streaming_url && <iframe title={`Live inspection of ${grant.title}`} src={inspectionRun.streaming_url} sandbox="allow-scripts allow-same-origin" referrerPolicy="no-referrer" style={{ width: "100%", height: 360, border: 0 }} />}
                  <div className="grant-actions"><button type="button" onClick={() => refreshFit(grant)} disabled={Boolean(busy) || Boolean(inspecting) || !profileReady}>Refresh fit</button><button type="button" onClick={() => inspectForm(grant)} disabled={Boolean(busy) || Boolean(inspecting)}>{inspecting ? "Inspecting…" : grant.inspection ? "Inspect again" : "Inspect application form"}</button><a href={grant.application_url || grant.source_url} target="_blank" rel="noreferrer">View source <span aria-hidden="true">↗</span></a><button type="button" onClick={() => prepareDraft(grant)} disabled={Boolean(busy) || Boolean(inspecting) || (!grant.inspection?.complete && !savedDrafts.some((item) => item.opportunity_id === grant.id))}>{drafting ? "Opening…" : savedDrafts.some((item) => item.opportunity_id === grant.id) ? "Open saved draft" : "Draft answers"}</button></div>
                  {isReviewing && review && <div className="review-panel" id="application-review"><div className="review-heading"><div><h5>Review your draft</h5><p>Check every answer against the grant’s actual form. Starting a run may submit this application to the provider.</p></div><span className="review-badge">Your call</span></div>
                    {Object.entries(review.answers).map(([question, answer]) => <div className="field review-field" key={question}><label htmlFor={`answer-${question}`}>{question}</label><textarea id={`answer-${question}`} rows={5} maxLength={10_000} disabled={Boolean(busy)} value={answer} onChange={(event) => setReview((current) => current ? { ...current, answers: { ...current.answers, [question]: event.target.value } } : null)} /><span className="field-help">{(() => { const field = grant.inspection?.questions.find((item) => item.label === question); return field ? [field.required ? "Required" : "Optional", field.help_text, field.max_words ? `${answer.trim() ? answer.trim().split(/\s+/).length : 0}/${field.max_words} words` : "", field.max_characters ? `${answer.length}/${field.max_characters} characters` : "", field.options.length ? `Choices: ${field.options.join("; ")}` : ""].filter(Boolean).join(" · ") : ""; })()}</span></div>)}
                    <p className="field-help">Saved revision {review.revision}. Save edits before leaving this page.</p>
                    {reviewStale && <div className="review-warning"><p>Your profile or the source changed since this draft was saved. Review all answers against the current details.</p><button type="button" disabled={Boolean(busy)} onClick={() => setReview({ ...review, source_version: grant.source_version || "", profile: { ...profile } })}>I reviewed the current details</button></div>}
                    <p className="field-help">This run cannot sign into a grant portal. If the provider requires login, open its portal yourself.</p>
                    {reviewNeedsWork && <div className="review-warning">{reviewProblems.map((problem) => <p key={problem}>{problem}</p>)}</div>}
                    {runResult && <p className={runResult.status === "not_submitted" || runResult.status === "unknown" ? "review-warning" : "field-help"} role="status">{runResult.message || "Submission status is unknown."}{runResult.evidence ? ` Evidence: ${runResult.evidence}` : ""}</p>}
                    <div className="review-actions"><button type="button" className="review-cancel" onClick={() => setReview(null)} disabled={Boolean(busy)}>Close draft</button><button type="button" className="review-cancel" onClick={persistDraft} disabled={Boolean(busy) || Boolean(reviewStale)}>Save draft</button><button type="button" className="review-submit" onClick={startApplication} disabled={Boolean(reviewNeedsWork) || Boolean(reviewStale) || Boolean(inspecting) || Boolean(busy) || Boolean(existingRun) || runUncertain}>{executing ? "Starting run…" : existingRun ? "Run already started" : "Start application run"}</button></div>
                  </div>}
                </article>;
              })}</div></> : <div className="empty-state"><div className="empty-illustration" aria-hidden="true"><div className="empty-sheet"><span /><span /><span /></div><div className="empty-lens">✳</div></div><h4>Your shortlist starts here.</h4><p>Tell us about your startup, then scan to see grants worth a closer look.</p></div>}
              {recentRuns.length > 0 && <section className="review-panel" aria-labelledby="recent-runs-heading"><div className="review-heading"><div><h4 id="recent-runs-heading">Recent application runs</h4><p>Saved run status remains available after you leave this page. Verify the final result in the grant portal.</p></div></div>
                {recentRuns.map((run) => <article className="grant-card" key={run.id}><div className="grant-copy"><h5>{run.grant_title}</h5><p><strong>{run.status === "submitted" ? "Confirmation evidence reported" : run.status === "not_submitted" ? "Not submitted" : run.status === "unknown" ? "Status unknown" : "In progress"}</strong> · {run.message}</p>{run.evidence && <p>Evidence: {run.evidence}</p>}{run.run_id && <p>Run ID: {run.run_id}</p>}</div><div className="grant-actions"><a href={run.application_url} target="_blank" rel="noreferrer">Check grant portal ↗</a>{run.status === "submitted" && <Link href="/thank-you">Thank you page</Link>}</div></article>)}
              </section>}
            </section>
          </div>
        </div>
      </main>
      <footer className="footer page-wrap"><Link href="/">AutoGrant<span className="brand-period">.</span></Link><p>Find your fit. Make your case.</p></footer>
    </div>
  );
}
