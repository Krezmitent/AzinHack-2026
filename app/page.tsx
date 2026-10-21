import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import LandingBrief from "@/components/LandingBrief";
import { verifiedReviews } from "@/lib/reviews";
import "./landing-redesign.css";

export const metadata: Metadata = {
  title: "Find Startup Grants That Fit | AutoGrant",
  description: "Discover startup grants, review their sources and fit, and prepare applications with AutoGrant."
};

export default function HomePage() {
  return (
    <div className="marketing-shell editorial-home">
      <SiteHeader />
      <main>
        <section className="editorial-hero" aria-labelledby="landing-heading">
          <div className="page-wrap editorial-hero__grid">
            <div className="editorial-hero__copy">
              <p className="editorial-hero__lead">A better way through the funding search.</p>
              <h1 id="landing-heading">Find grants.<br />Know <em>why.</em></h1>
              <p className="editorial-hero__intro">AutoGrant turns scattered funding pages into a shortlist you can actually evaluate. See the source, understand the fit, and decide what deserves your time.</p>
              <div className="editorial-hero__actions">
                <Link className="editorial-button" href="/signup">Start your search <span aria-hidden="true">↗</span></Link>
                <Link className="editorial-link" href="/#how-it-works">See the workflow</Link>
              </div>
              <p className="editorial-hero__assurance"><span aria-hidden="true">✳</span> Every application starts with your review.</p>
            </div>
            <LandingBrief />
          </div>
          <div className="page-wrap editorial-hero__lower"><span>Source linked discovery</span><span>Fit with context</span><span>Founder’s final say</span></div>
        </section>

        <section className="editorial-process page-wrap" id="how-it-works" aria-labelledby="how-heading">
          <div className="editorial-section-intro"><h2 id="how-heading">A clearer path from search to application.</h2><p>Finding a promising grant is only the beginning. The real work is checking the rules and making a case that holds up.</p></div>
          <div className="editorial-process__rows">
            <article><span>01</span><div><h3>Build your profile</h3><p>Tell us your sector, location, stage, and what you are building.</p></div><b aria-hidden="true">↗</b></article>
            <article><span>02</span><div><h3>Review the evidence</h3><p>See opportunities with source pages, fit notes, and open eligibility questions.</p></div><b aria-hidden="true">↗</b></article>
            <article><span>03</span><div><h3>Prepare deliberately</h3><p>Inspect the application, edit the draft, and choose when to proceed.</p></div><b aria-hidden="true">↗</b></article>
          </div>
        </section>

        <section className="editorial-principle" id="why-autogrant" aria-labelledby="principle-heading"><div className="page-wrap editorial-principle__grid"><div><p className="editorial-principle__kicker">The principle</p><h2 id="principle-heading">A shortlist should come with receipts.</h2></div><div className="editorial-principle__detail"><p>A score alone cannot tell you whether a grant is worth pursuing. AutoGrant keeps the original source and the unresolved questions next to each recommendation.</p><ul><li><span>01</span> Open the programme page we found.</li><li><span>02</span> Check what is known and what remains uncertain.</li><li><span>03</span> Edit every application answer before you act.</li></ul><Link href="/signup">Create a profile <span aria-hidden="true">↗</span></Link></div></div></section>

        <section className="editorial-reviews page-wrap" id="reviews" aria-labelledby="reviews-heading"><div className="editorial-section-intro"><h2 id="reviews-heading">Founder feedback</h2><p>We publish founders’ words only with their approval and attribution.</p></div>{verifiedReviews.length ? <div className="editorial-reviews__grid">{verifiedReviews.map((review) => <figure key={`${review.name}-${review.quote}`}><blockquote>“{review.quote}”</blockquote><figcaption><strong>{review.name}</strong><span>{review.role}</span>{review.sourceUrl && <a href={review.sourceUrl} target="_blank" rel="noreferrer">Read original review</a>}</figcaption></figure>)}</div> : <p className="editorial-reviews__empty">No founder reviews have been published yet.</p>}</section>

        <section className="editorial-final page-wrap"><div><p>Ready when you are.</p><h2>Make your next application count.</h2></div><Link className="editorial-button editorial-button--light" href="/signup">Create your profile <span aria-hidden="true">↗</span></Link></section>
      </main>
      <SiteFooter />
    </div>
  );
}
