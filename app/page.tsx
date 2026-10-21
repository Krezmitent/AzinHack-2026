import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import LandingBrief from "@/components/LandingBrief";
import LandingMotion from "@/components/LandingMotion";
import { verifiedReviews } from "@/lib/reviews";
import "./landing-redesign.css";

export const metadata: Metadata = {
  title: "A clearer route to your next grant",
  description: "Find startup grants, understand the fit, and prepare your next application with AutoGrant."
};

const features = [
  { kind: "search", title: "Find the opportunities.", copy: "Search public funding pages around your startup’s sector, location, and stage.", line: "Your startup, at the centre of the search", rows: ["Sector and location", "Stage and funding needs", "Original programme pages"] },
  { kind: "fit", title: "Understand the fit.", copy: "See the reasoning behind a match and the eligibility questions that still need checking.", line: "A reason behind every recommendation", rows: ["What looks relevant", "What needs verification", "The source, always in reach"] },
  { kind: "draft", title: "Make your case.", copy: "Inspect the application questions, prepare a draft, and shape every answer before proceeding.", line: "A starting point for your next application", rows: ["The actual form questions", "Editable draft answers", "Your review before a run"] }
];

export default function HomePage() {
  return (
    <div className="marketing-shell modern-home">
      <LandingMotion />
      <SiteHeader />
      <main>
        <section className="modern-hero" aria-labelledby="landing-heading">
          <div className="modern-hero__ribbons modern-hero__ribbons--left" aria-hidden="true"><i /><i /><i /><i /><i /></div>
          <div className="modern-hero__ribbons modern-hero__ribbons--right" aria-hidden="true"><i /><i /><i /><i /><i /></div>
          <div className="page-wrap modern-hero__content">
            <p className="modern-hero__badge"><span aria-hidden="true">✳</span> Built for the people building what’s next</p>
            <h1 id="landing-heading">A clearer route to<br />your next grant.</h1>
            <p className="modern-hero__intro">Find funding that fits what you’re building. AutoGrant brings the opportunities, the evidence, and your application into one place.</p>
            <div className="modern-actions"><Link className="modern-button modern-button--primary" href="/signup">Find my grants <span aria-hidden="true">↗</span></Link><a className="modern-button modern-button--secondary" href="#how-it-works">See how it works</a></div>
            <p className="modern-hero__note">You make the decisions. AutoGrant helps with the groundwork.</p>
          </div>
          <div className="modern-hero__path page-wrap"><span>Discover</span><i aria-hidden="true" /><span>Understand</span><i aria-hidden="true" /><span>Prepare</span></div>
        </section>

        <section className="modern-workflow page-wrap" id="how-it-works" aria-labelledby="workflow-heading">
          <div className="modern-section-heading"><p>From possibility to a plan</p><h2 id="workflow-heading">Less searching in circles.<br />More moving forward.</h2><p>Give your funding search a direction, then work through the details with the original sources in view.</p></div>
          <svg className="modern-route-lines" viewBox="0 0 1440 560" fill="none" preserveAspectRatio="none" aria-hidden="true"><path d="M-90 86C130 86 115 214 335 214S540 80 720 116s174 223 354 194 194-88 464-88"/><path d="M-90 118C130 118 115 246 335 246S540 112 720 148s174 223 354 194 194-88 464-88"/><path d="M-90 150C130 150 115 278 335 278S540 144 720 180s174 223 354 194 194-88 464-88"/><path d="M-90 182C130 182 115 310 335 310S540 176 720 212s174 223 354 194 194-88 464-88"/></svg>
          <LandingBrief />
        </section>

        <section className="modern-capabilities" id="why-autogrant" aria-labelledby="capabilities-heading"><div className="page-wrap"><div className="modern-capabilities__heading"><p>The whole funding workflow</p><h2 id="capabilities-heading">Good opportunities deserve<br />a better process.</h2></div><div className="modern-feature-grid">{features.map((feature) => <article className={`modern-feature modern-feature--${feature.kind}`} key={feature.kind}><div className="modern-feature__visual" aria-hidden="true"><div className="modern-feature__prompt"><span>{feature.kind === "search" ? "⌕" : feature.kind === "fit" ? "✓" : "✎"}</span>{feature.line}</div><div className="modern-feature__paper">{feature.rows.map((row, i) => <div key={row}><span className={`modern-feature__mini mini-${i}`} />{row}<b>✓</b></div>)}</div></div><h3>{feature.title}</h3><p>{feature.copy}</p></article>)}</div></div></section>

        <section className="modern-control page-wrap" aria-labelledby="control-heading"><div className="modern-control__copy"><p className="modern-section-label">The final say stays with you</p><h2 id="control-heading">Your startup.<br />Your story.<br />Your call.</h2><p>AutoGrant helps you find and prepare. You check the programme rules, edit the answers, and decide when an application run begins.</p><Link className="modern-button modern-button--secondary" href="/signup">Create your profile <span aria-hidden="true">↗</span></Link></div><div className="modern-control__visual"><div className="modern-review"><div className="modern-review__top"><span className="modern-review__avatar">A</span><div><strong>Application review</strong><span>Before you proceed</span></div><b>In your hands</b></div><h3>Make it sound like you.</h3><p>Review the draft against the actual application questions. Change any answer before you move forward.</p><div className="modern-review__line"><span>Source checked</span><b>✓</b></div><div className="modern-review__line"><span>Answers reviewed</span><b>✓</b></div><div className="modern-review__approval"><span aria-hidden="true">↗</span> You choose the next step.</div></div><div className="modern-control__caption"><span aria-hidden="true">✳</span> Support through the work. Control over the outcome.</div></div></section>

        <section className="modern-manifesto" aria-labelledby="manifesto-heading"><div className="page-wrap modern-manifesto__inner"><p>BETTER FUNDING STARTS WITH A CLEARER VIEW</p><h2 id="manifesto-heading">Find your fit.<br /><span>Shape what comes next.</span></h2><div className="modern-manifesto__route" aria-hidden="true"><i /><i /><i /><i /><i /></div></div></section>

        <section className="modern-tiles page-wrap" aria-labelledby="tiles-heading"><div className="modern-tiles__copy"><p className="modern-section-label">ONE WORKSPACE, THE PIECES IN VIEW</p><h2 id="tiles-heading">Your funding search, all connected.</h2><p>Keep your startup details, relevant opportunities, eligibility notes, source pages, and draft answers together as you move from discovery to application.</p></div><div className="modern-tiles__grid" aria-label="Illustration of the AutoGrant funding workflow"><div className="modern-tile modern-tile--profile"><span className="modern-tile__icon" aria-hidden="true">A</span><strong>Startup profile</strong><small>Your details</small></div><div className="modern-tile modern-tile--sector"><span className="modern-tile__icon" aria-hidden="true">⌕</span><strong>Sector</strong><small>Climate tech</small></div><div className="modern-tile modern-tile--location"><span className="modern-tile__icon" aria-hidden="true">◎</span><strong>Location</strong><small>India</small></div><div className="modern-tile modern-tile--grants"><span className="modern-tile__icon" aria-hidden="true">↗</span><strong>Open grants</strong><small>Original programme pages</small></div><div className="modern-tile modern-tile--fit"><span className="modern-tile__icon" aria-hidden="true">✓</span><strong>Fit notes</strong><small>Why it may fit</small></div><div className="modern-tile modern-tile--eligibility"><span className="modern-tile__icon" aria-hidden="true">?</span><strong>Eligibility</strong><small>What to verify</small></div><div className="modern-tile modern-tile--sources"><span className="modern-tile__icon" aria-hidden="true">↗</span><strong>Source links</strong><small>Check the provider</small></div><div className="modern-tile modern-tile--form"><span className="modern-tile__icon" aria-hidden="true">▤</span><strong>Application form</strong><small>Real questions</small></div><div className="modern-tile modern-tile--draft"><span className="modern-tile__icon" aria-hidden="true">✎</span><strong>Draft answers</strong><small>Ready for your review</small></div></div></section>

        {verifiedReviews.length > 0 && <section className="modern-reviews page-wrap" id="reviews"><div className="modern-section-heading"><h2>In founders’ own words.</h2></div><div className="modern-reviews__grid">{verifiedReviews.map((review) => <figure key={`${review.name}-${review.quote}`}><blockquote>“{review.quote}”</blockquote><figcaption><strong>{review.name}</strong><span>{review.role}</span>{review.sourceUrl && <a href={review.sourceUrl} target="_blank" rel="noreferrer">Read original review</a>}</figcaption></figure>)}</div></section>}

        <section className="modern-final page-wrap" aria-labelledby="final-heading"><h2 id="final-heading">Build what’s next.<br />Find what funds it.</h2><div className="modern-final__burst" aria-hidden="true"><i /><i /><i /><i /><i /></div><div className="modern-final__cta"><Link className="modern-button modern-button--primary modern-button--explosive" href="/signup">Find my grants <span aria-hidden="true">↗</span></Link></div></section>
      </main>
      <SiteFooter />
    </div>
  );
}
