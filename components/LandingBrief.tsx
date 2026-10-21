"use client";

import { useState } from "react";

type Sector = "Climate" | "Fintech" | "Health";

const briefs: Record<Sector, { focus: string; reason: string; check: string; note: string }> = {
  Climate: {
    focus: "Climate technology",
    reason: "Look for programmes backing pilots, adaptation, and measurable environmental outcomes.",
    check: "Does the programme fund your current pilot stage?",
    note: "A climate focus can narrow the search. Programme rules still decide eligibility."
  },
  Fintech: {
    focus: "Financial technology",
    reason: "Look for programmes interested in access, infrastructure, and responsible financial services.",
    check: "Are regulated financial products allowed by the funder?",
    note: "Sector fit is one signal. Licensing and geography can change eligibility."
  },
  Health: {
    focus: "Health technology",
    reason: "Look for programmes supporting clinical access, public health, and care delivery.",
    check: "Is your product at the required validation stage?",
    note: "A relevant theme does not confirm clinical or regulatory eligibility."
  }
};

export default function LandingBrief() {
  const [sector, setSector] = useState<Sector>("Climate");
  const brief = briefs[sector];

  return (
    <div className="brief-demo" aria-label="Illustrative funding brief">
      <div className="brief-demo__topline">
        <span className="brief-demo__seal" aria-hidden="true"><span /></span>
        <span>Inside the funding desk</span>
        <span className="brief-demo__edition">Sample view</span>
      </div>
      <div className="brief-demo__body">
        <div className="brief-demo__heading">
          <span>Start with your story</span>
          <h2>Make the search yours.</h2>
          <p>Choose a field to see how a funding brief changes.</p>
        </div>
        <div className="brief-demo__choices" role="group" aria-label="Choose an example startup field">
          {(Object.keys(briefs) as Sector[]).map((name) => (
            <button key={name} type="button" aria-pressed={sector === name} onClick={() => setSector(name)}>{name}</button>
          ))}
        </div>
        <div className="brief-demo__sheet" aria-live="polite">
          <div className="brief-demo__sheet-head"><span>Search brief</span><span>01 / 03</span></div>
          <h3>{brief.focus}</h3>
          <div className="brief-demo__entry"><span className="brief-demo__entry-symbol">↗</span><div><strong>Where to look</strong><p>{brief.reason}</p></div></div>
          <div className="brief-demo__entry"><span className="brief-demo__entry-symbol">?</span><div><strong>What to verify</strong><p>{brief.check}</p></div></div>
          <div className="brief-demo__verdict"><span className="brief-demo__verdict-dot" /><p>{brief.note}</p></div>
        </div>
      </div>
      <p className="brief-demo__foot">Illustrative example. Real opportunities link to their original source.</p>
    </div>
  );
}
