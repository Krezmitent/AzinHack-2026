"use client";

import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from "react";
import { signInAnonymously } from "firebase/auth";
import { doc, setDoc } from "firebase/firestore";
import { firebaseServices } from "@/lib/firebase";
import { discoverGrants, draftApplication, executeApplication, scoreGrant } from "@/lib/api";
import type { Grant, StartupProfile } from "@/lib/types";

const initialProfile: StartupProfile = { sector: "", revenue: "", demographics: "", pitchDeckText: "" };

export default function Dashboard() {
  const [profile, setProfile] = useState<StartupProfile>(initialProfile);
  const [grants, setGrants] = useState<Grant[]>([]);
  const [busy, setBusy] = useState<"save" | "discover" | string | null>(null);
  const [notice, setNotice] = useState("Connect a profile, then find grants matched to your startup.");
  const [uid, setUid] = useState<string | null>(null);

  useEffect(() => {
    try {
      const { auth } = firebaseServices();
      signInAnonymously(auth)
        .then(({ user }) => setUid(user.uid))
        .catch(() => setNotice("Firebase sign-in is unavailable. Check your public Firebase environment variables."));
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Firebase is unavailable.");
    }
  }, []);

  const highScoreCount = useMemo(() => grants.filter((grant) => (grant.match_score ?? 0) >= 70).length, [grants]);

  function update(field: keyof StartupProfile, value: string) {
    setProfile((current) => ({ ...current, [field]: value }));
  }

  async function uploadPitchDeck(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith(".txt") && file.type !== "text/plain") {
      setNotice("Please upload a plain-text (.txt) pitch deck.");
      return;
    }
    update("pitchDeckText", await file.text());
  }

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (!uid) return setNotice("Waiting for Firebase authentication…");
    setBusy("save");
    try {
      const { db } = firebaseServices();
      await setDoc(doc(db, "users", uid), {
        ...profile,
        updatedAt: new Date().toISOString()
      }, { merge: true });
      setNotice("Startup profile saved securely to Firestore.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not save your profile.");
    } finally { setBusy(null); }
  }

  async function findGrants() {
    setBusy("discover");
    try {
      const discovered = await discoverGrants();
      const scored = await Promise.all(discovered.grants.map(async (grant) => ({
        ...grant,
        ...(await scoreGrant(grant, profile))
      })));
      setGrants(scored.sort((a, b) => (b.match_score ?? 0) - (a.match_score ?? 0)));
      setNotice(`Found and scored ${scored.length} grant opportunities.`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not discover grants.");
    } finally { setBusy(null); }
  }

  async function apply(grant: Grant) {
    if (!confirm(`Draft and submit an application to ${grant.title}? TinyFish may use only vault credentials you approve.`)) return;
    const key = grant.source_url;
    setBusy(key);
    try {
      const questions = ["Describe your startup and the problem it solves.", "How will you use this grant?"];
      const { answers } = await draftApplication(grant, profile, questions);
      const label = window.prompt("TinyFish Vault credential label (optional; never enter a password):")?.trim();
      const result = await executeApplication(grant, answers, label ? [label] : []);
      setNotice(`Application run started for ${grant.title}. ${JSON.stringify(result.run).slice(0, 140)}`);
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not start the application run.");
    } finally { setBusy(null); }
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 sm:px-8">
      <header className="mb-8 flex flex-col gap-4 border-b border-slate-800 pb-7 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="text-sm font-semibold uppercase tracking-[.25em] text-cyan-400">AutoGrant AI</p><h1 className="mt-2 text-3xl font-bold tracking-tight sm:text-4xl">Funding, found and applied for.</h1></div>
        <div className="rounded-full border border-slate-700 bg-slate-900 px-4 py-2 text-sm text-slate-300">{highScoreCount} high-confidence matches</div>
      </header>

      <p aria-live="polite" className="mb-6 rounded-lg border border-cyan-900/70 bg-cyan-950/30 p-3 text-sm text-cyan-100">{notice}</p>

      <div className="grid gap-6 lg:grid-cols-[.9fr_1.4fr]">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-2xl shadow-slate-950/30">
          <h2 className="text-xl font-semibold">Startup profile</h2><p className="mt-1 text-sm text-slate-400">This context is used only to score grants and draft answers.</p>
          <form onSubmit={saveProfile} className="mt-5 space-y-4">
            <label className="block text-sm font-medium">Sector<input required value={profile.sector} onChange={(e) => update("sector", e.target.value)} placeholder="Climate tech, fintech, health…" /></label>
            <label className="block text-sm font-medium">Annual revenue / stage<input required value={profile.revenue} onChange={(e) => update("revenue", e.target.value)} placeholder="Pre-revenue, $120k ARR…" /></label>
            <label className="block text-sm font-medium">Founder demographics<textarea required rows={3} value={profile.demographics} onChange={(e) => update("demographics", e.target.value)} placeholder="Optional eligibility-relevant details, location, ownership…" /></label>
            <label className="block text-sm font-medium">Plain-text pitch deck<textarea required rows={7} value={profile.pitchDeckText} onChange={(e) => update("pitchDeckText", e.target.value)} placeholder="Paste your pitch deck or upload a .txt file." /></label>
            <input aria-label="Upload a plain text pitch deck" type="file" accept=".txt,text/plain" onChange={uploadPitchDeck} className="text-xs" />
            <button disabled={busy === "save"} className="w-full rounded-lg bg-slate-100 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-white">{busy === "save" ? "Saving…" : "Save profile"}</button>
          </form>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5 shadow-2xl shadow-slate-950/30">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-xl font-semibold">Grants match</h2><p className="mt-1 text-sm text-slate-400">Live discovery with criteria-aware compatibility scoring.</p></div><button onClick={findGrants} disabled={busy === "discover" || !profile.sector || !profile.pitchDeckText} className="rounded-lg bg-cyan-400 px-4 py-2.5 text-sm font-bold text-slate-950 hover:bg-cyan-300">{busy === "discover" ? "Discovering…" : "Discover grants"}</button></div>
          <div className="mt-5 space-y-3">
            {grants.length === 0 && <div className="rounded-xl border border-dashed border-slate-700 p-8 text-center text-sm text-slate-500">Save a profile and discover live opportunities to populate this view.</div>}
            {grants.map((grant) => <article key={grant.source_url} className="rounded-xl border border-slate-800 bg-slate-950/60 p-4"><div className="flex flex-col gap-3 sm:flex-row sm:justify-between"><div><h3 className="font-semibold">{grant.title}</h3><p className="mt-1 text-sm text-slate-400">{grant.match_reason || "Eligibility parsed from source."}</p></div><div className="text-2xl font-bold text-cyan-400">{grant.match_score ?? 0}%</div></div><p className="mt-3 text-xs text-slate-500">Criteria: {grant.eligibility_criteria.slice(0, 3).join(" · ") || "Review source"}</p><div className="mt-4 flex items-center gap-3"><a className="text-sm text-cyan-300 underline" href={grant.application_url || grant.source_url} target="_blank" rel="noreferrer">View source</a><button onClick={() => apply(grant)} disabled={busy === grant.source_url || (grant.match_score ?? 0) < 70} className="ml-auto rounded-lg bg-emerald-400 px-3 py-2 text-sm font-bold text-emerald-950 hover:bg-emerald-300">{busy === grant.source_url ? "Starting…" : "One-Click Apply"}</button></div></article>)}
          </div>
        </section>
      </div>
    </main>
  );
}
