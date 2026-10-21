"use client";

import { useCallback, useEffect, useState } from "react";
import { controlFundingWatch, createFundingWatch, loadFundingRadar, loadSavedOpportunity, markFundingEventRead, updateTrackedApplication } from "@/lib/api";
import type { FundingEvent, FundingRadarData, Grant, TrackedApplication } from "@/lib/types";

const empty: FundingRadarData = { watches: [], events: [], applications: [] };
const statuses: TrackedApplication["status"][] = ["draft", "submitted", "under_review", "information_requested", "awarded", "rejected", "withdrawn"];

export default function FundingRadar({ grants, onMessage, onGrantUpdate }: { grants: Grant[]; onMessage: (message: string, tone: "success" | "error" | "info") => void; onGrantUpdate: (grant: Grant) => void }) {
  const [data, setData] = useState(empty);
  const [busy, setBusy] = useState("");
  const [cadence, setCadence] = useState<"daily" | "six_hourly">("daily");
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  const refresh = useCallback(async () => { try { setData(await loadFundingRadar()); } catch { /* Leave the last saved view visible through temporary network errors. */ } }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 30_000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function act(key: string, action: () => Promise<unknown>, message: string) {
    if (busy) return;
    setBusy(key);
    try { await action(); await refresh(); onMessage(message, "success"); }
    catch (error) { onMessage(error instanceof Error ? error.message : "Could not update the funding desk.", "error"); }
    finally { setBusy(""); }
  }

  async function addWatch(grant: Grant) {
    if (!grant.id) return;
    await act(`watch:${grant.id}`, () => createFundingWatch({ type: "fetch", opportunity_id: grant.id, cadence, timezone }), "Programme watch saved. TinyFish will report meaningful changes here.");
  }

  async function track(grant: Grant) {
    if (!grant.id) return;
    await act(`track:${grant.id}`, () => updateTrackedApplication(grant.id!, { status: "draft", note: "", expected_revision: 0, timezone }), "Application added to your tracker.");
  }

  async function saveStatus(application: TrackedApplication, status: TrackedApplication["status"], note: string) {
    await act(`app:${application.id}`, () => updateTrackedApplication(application.id, { status, note, expected_revision: application.revision, timezone }), "Application status saved.");
  }

  async function readEvent(event: FundingEvent) {
    if (event.read) return;
    await act(`event:${event.id}`, async () => {
      await markFundingEventRead(event.id);
      if (event.opportunity_id && event.kind === "funding_change") onGrantUpdate((await loadSavedOpportunity(event.opportunity_id)).grant);
    }, "Update marked as reviewed.");
  }

  return <section className="matches-panel funding-radar" id="funding-radar" aria-labelledby="funding-radar-heading">
    <div className="matches-heading"><div><h3 id="funding-radar-heading">Funding radar</h3><p>TinyFish checks public programme pages and brings material changes into this inbox.</p></div><label className="field-help">Check cadence <select value={cadence} onChange={(event) => setCadence(event.target.value as "daily" | "six_hourly")}><option value="daily">Daily · about $0.15/month</option><option value="six_hourly">Every 6 hours · about $0.60/month</option></select></label></div>
    <p className="field-help">TinyFish monitor usage is billed by TinyFish; underlying plan allowances may apply. Paused watches still count toward your limit.</p>
    {grants.length > 0 && <div className="radar-opportunities"><h4>Watch a programme</h4>{grants.map((grant) => <article className="radar-row" key={grant.id || grant.source_url}><div><strong>{grant.title}</strong><p>{grant.source_url}</p></div><div className="grant-actions"><button type="button" disabled={!grant.id || Boolean(busy) || data.watches.some((watch) => watch.opportunity_id === grant.id && watch.status !== "deleted")} onClick={() => void addWatch(grant)}>{busy === `watch:${grant.id}` ? "Saving…" : "Watch with TinyFish"}</button><button type="button" disabled={!grant.id || Boolean(busy) || data.applications.some((app) => app.id === grant.id)} onClick={() => void track(grant)}>{busy === `track:${grant.id}` ? "Saving…" : "Track application"}</button></div></article>)}</div>}
    <div className="radar-columns">
      <div><h4>Programme watches <span className="optional">{data.watches.length}</span></h4>{data.watches.length ? data.watches.map((watch) => <article className="radar-row" key={watch.id}><div><strong>{watch.target}</strong><p>{watch.status}{watch.last_checked_at ? ` · checked ${new Date(watch.last_checked_at).toLocaleString()}` : ""}{watch.last_error ? ` · ${watch.last_error}` : ""}</p>{watch.check_status && <p>Manual check: {watch.check_status}</p>}</div><div className="grant-actions">{watch.monitor_id && <><button type="button" disabled={Boolean(busy)} onClick={() => void act(`check:${watch.id}`, () => controlFundingWatch(watch.id, "check"), "A TinyFish check was queued.")}>Check now</button><button type="button" disabled={Boolean(busy)} onClick={() => void act(`pause:${watch.id}`, () => controlFundingWatch(watch.id, watch.status === "paused" ? "resume" : "pause"), watch.status === "paused" ? "Watch resumed." : "Watch paused.")}>{watch.status === "paused" ? "Resume" : "Pause"}</button></>}{(watch.status === "unknown" || watch.monitor_id) && <button type="button" disabled={Boolean(busy)} onClick={() => void act(`sync:${watch.id}`, () => controlFundingWatch(watch.id, "sync"), "Watch status synced.")}>Sync</button>}{watch.status === "failed" && <button type="button" disabled={Boolean(busy)} onClick={() => void act(`delete:${watch.id}`, () => controlFundingWatch(watch.id, "delete"), "Failed watch removed.")}>Remove</button>}</div></article>) : <p className="field-help">No programme watches yet.</p>}</div>
      <div><h4>Change inbox <span className="optional">{data.events.filter((event) => !event.read).length} new</span></h4>{data.events.length ? data.events.map((event) => <article className={`radar-event ${event.read ? "is-read" : ""}`} key={event.id}><div><strong>{event.title}</strong><p>{event.message}</p>{event.changed_fields?.length ? <p>Changed: {event.changed_fields.join(", ")}</p> : null}{event.source_url && <a href={event.source_url} target="_blank" rel="noreferrer">Review source ↗</a>}<small>{new Date(event.created_at).toLocaleString()}</small></div>{!event.read && <button type="button" disabled={Boolean(busy)} onClick={() => void readEvent(event)}>Mark reviewed</button>}</article>) : <p className="field-help">Meaningful programme changes and deadline reminders will appear here.</p>}</div>
    </div>
    <div><h4>Application tracker</h4>{data.applications.length ? data.applications.map((application) => <ApplicationRow key={application.id} application={application} busy={busy === `app:${application.id}`} onSave={(status, note) => void saveStatus(application, status, note)} />) : <p className="field-help">Track an opportunity above to record founder-reported status and deadline reminders.</p>}</div>
  </section>;
}

function ApplicationRow({ application, busy, onSave }: { application: TrackedApplication; busy: boolean; onSave: (status: TrackedApplication["status"], note: string) => void }) {
  const [status, setStatus] = useState(application.status);
  const [note, setNote] = useState(application.note || "");
  useEffect(() => { setStatus(application.status); setNote(application.note || ""); }, [application.revision, application.status, application.note]);
  return <article className="radar-row"><div><strong>{application.grant_title}</strong><p>{application.deadline_date ? `Provider deadline: ${application.deadline_date}` : "No confirmed deadline saved"} · {application.status_source === "submission_confirmation" ? "Submission confirmation" : "Founder reported"}</p><label className="field-help">Status <select value={status} onChange={(event) => setStatus(event.target.value as TrackedApplication["status"])}>{statuses.map((item) => <option key={item} value={item}>{item.replaceAll("_", " ")}</option>)}</select></label><label className="field-help">Note <input maxLength={2000} value={note} onChange={(event) => setNote(event.target.value)} placeholder="Next step or provider response" /></label></div><button type="button" disabled={busy || (status === application.status && note === (application.note || ""))} onClick={() => onSave(status, note)}>{busy ? "Saving…" : "Save status"}</button></article>;
}
