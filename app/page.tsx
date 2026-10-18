import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import { verifiedReviews } from "@/lib/reviews";

export const metadata: Metadata = {
  title: "Find Startup Grants That Fit | AutoGrant",
  description: "Discover startup grants, see why they may fit your business, and prepare application answers with AutoGrant."
};

const steps = [
  { number: "01", title: "Tell us your story", copy: "Add your sector, stage, and a plain-text overview of what you’re building." },
  { number: "02", title: "See what fits", copy: "Scan grant opportunities and review a ranked shortlist with eligibility notes." },
  { number: "03", title: "Make your case", copy: "Prepare draft answers, edit them yourself, and decide when to start an application run." }
];

export default function HomePage() {
  return (
    <div className="marketing-shell">
      <SiteHeader />
      <main>
        <section className="landing-hero" aria-labelledby="landing-heading">
          <div className="page-wrap landing-hero-grid">
            <div className="landing-hero-copy">
              <h1 id="landing-heading">A better way to find your next grant.</h1>
              <p>Find opportunities that fit your startup, understand the match, and get a head start on the application.</p>
              <div className="landing-actions"><Link className="landing-primary" href="/signup">Create your profile <span aria-hidden="true">↗</span></Link><Link className="landing-secondary" href="/#how-it-works">See how it works</Link></div>
              <p className="landing-small-print">You review every draft before an application run starts.</p>
            </div>
            <div className="landing-visual" aria-hidden="true">
              <div className="landing-ring landing-ring-one" /><div className="landing-ring landing-ring-two" />
              <div className="landing-file">
                <div className="landing-file-top"><span>AutoGrant</span><span>Funding desk</span></div>
                <div className="landing-file-title">Your path<br />to the right fit.</div>
                <div className="landing-file-row"><span>01</span><strong>Your story</strong><i /></div>
                <div className="landing-file-row"><span>02</span><strong>Grant shortlist</strong><i /></div>
                <div className="landing-file-row"><span>03</span><strong>First draft</strong><i /></div>
                <div className="landing-file-bottom">Built around your startup, not a generic search.</div>
              </div>
              <div className="landing-star">✳</div>
            </div>
          </div>
        </section>

        <section className="landing-section page-wrap" id="how-it-works" aria-labelledby="how-heading">
          <div className="section-heading"><h2 id="how-heading">From idea to shortlist, without the spreadsheet.</h2><p>AutoGrant keeps the search, the match, and the first draft in one place.</p></div>
          <div className="steps-grid">{steps.map((step) => <article className="step" key={step.number}><span className="step-number">{step.number}</span><h3>{step.title}</h3><p>{step.copy}</p></article>)}</div>
        </section>

        <section className="why-section" id="why-autogrant" aria-labelledby="why-heading">
          <div className="page-wrap why-grid">
            <div className="why-title"><h2 id="why-heading">Good funding deserves a closer look.</h2><p>Grant fit is more than a keyword match. AutoGrant gives you a starting point you can inspect.</p><Link href="/signup">Start your search <span aria-hidden="true">↗</span></Link></div>
            <div className="why-list"><div><span className="why-icon">⌕</span><h3>Search beyond your bookmarks</h3><p>Bring fresh grant opportunities into one shortlist instead of juggling tabs and spreadsheets.</p></div><div><span className="why-icon">✳</span><h3>Understand the match</h3><p>See a score, a short reason, and the source criteria so you can judge each opportunity yourself.</p></div><div><span className="why-icon">✎</span><h3>Keep the final say</h3><p>Edit draft answers before you start an application run. Your application remains your decision.</p></div></div>
          </div>
        </section>

        <section className="landing-section reviews-section page-wrap" id="reviews" aria-labelledby="reviews-heading">
          <div className="section-heading"><h2 id="reviews-heading">What founders are saying</h2><p>Feedback from people who have actually used AutoGrant.</p></div>
          {verifiedReviews.length ? <div className="review-grid">{verifiedReviews.map((review) => <figure className="review-card" key={`${review.name}-${review.quote}`}><blockquote>“{review.quote}”</blockquote><figcaption><strong>{review.name}</strong><span>{review.role}</span>{review.sourceUrl && <a href={review.sourceUrl} target="_blank" rel="noreferrer">Read the original review ↗</a>}</figcaption></figure>)}</div> : <div className="review-empty"><span aria-hidden="true">“</span><div><h3>Real words only.</h3><p>We haven’t published verified founder reviews yet. We’ll add them when reviewers approve their quotes.</p></div></div>}
        </section>

        <section className="landing-cta page-wrap"><div><h2>Find a better fit for your next application.</h2><p>Start with your story. See where it can take you.</p></div><Link className="landing-primary" href="/signup">Get started <span aria-hidden="true">↗</span></Link></section>
      </main>
      <SiteFooter />
    </div>
  );
}
