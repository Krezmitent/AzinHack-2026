"use client";

import { useState } from "react";

const steps = [
  { name: "Discover", title: "Start with what you’re building.", description: "Your profile gives the search its direction. Sector, location, and stage help surface opportunities worth a closer look.", prompt: "Find funding for my startup", focus: "Your startup profile", rows: [{label:"Sector",value:"Climate technology"},{label:"Based in",value:"India"},{label:"Stage",value:"Pilot stage"}], note: "A starting point for a more relevant search.", color: "orange" },
  { name: "Understand", title: "Get the context behind the match.", description: "A promising title is only the beginning. Review the original page, the fit notes, and any eligibility details that are still unknown.", prompt: "Help me understand the fit", focus: "Opportunity review", rows: [{label:"Sector relevance",value:"Review fit notes"},{label:"Programme rules",value:"Open original source"},{label:"Eligibility",value:"Check unknowns"}], note: "A fit assessment is guidance, not an eligibility guarantee.", color: "purple" },
  { name: "Prepare", title: "Turn your story into a first draft.", description: "Inspect the real application questions, prepare answers from your profile, and edit them into a version you’re ready to stand behind.", prompt: "Help me prepare my application", focus: "Application workspace", rows: [{label:"Form questions",value:"Inspect the application"},{label:"Your answers",value:"Prepare and edit"},{label:"Next step",value:"Review before proceeding"}], note: "You review the draft before an application run begins.", color: "blue" }
];

export default function LandingBrief() {
  const [active, setActive] = useState(0);
  const step = steps[active];
  return <div className={`journey journey--${step.color}`}>
    <div className="journey__nav" role="group" aria-label="Explore the AutoGrant workflow">{steps.map((item, index) => <button key={item.name} type="button" aria-pressed={active === index} onClick={() => setActive(index)}><span className="journey__step-dot" aria-hidden="true" />{item.name}<span className="journey__nav-arrow" aria-hidden="true">↗</span></button>)}</div>
    <div className="journey__stage" aria-live="polite"><div className="journey__copy"><span className="journey__icon" aria-hidden="true">{active === 0 ? "⌕" : active === 1 ? "✓" : "✎"}</span><h3>{step.title}</h3><p>{step.description}</p><span className="journey__sample">An illustrative walkthrough</span></div><div className="journey__visual"><div className="journey__prompt"><span aria-hidden="true">✳</span>{step.prompt}</div><div className="journey__document"><div className="journey__document-title"><span className="journey__document-symbol" aria-hidden="true">A</span><div><strong>{step.focus}</strong><span>AutoGrant workspace</span></div><i aria-hidden="true">•••</i></div>{step.rows.map((row) => <div className="journey__row" key={row.label}><span>{row.label}</span><strong>{row.value}</strong></div>)}<div className="journey__document-note"><span aria-hidden="true">↗</span>{step.note}</div></div></div></div>
  </div>;
}
