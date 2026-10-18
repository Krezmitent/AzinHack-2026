import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="page-wrap site-footer-inner">
        <div>
          <Link className="brand footer-brand" href="/" aria-label="AutoGrant home">
            <span className="brand-mark" aria-hidden="true"><span /><span /><span /><span /></span>
            <span>AutoGrant<span className="brand-period">.</span></span>
          </Link>
          <p>Find your fit. Make your case.</p>
        </div>
        <nav aria-label="Footer navigation">
          <Link href="/#how-it-works">How it works</Link>
          <Link href="/#reviews">Reviews</Link>
          <Link href="/dashboard">Grant board</Link>
          <Link href="/login">Log in</Link>
          <Link href="/signup">Sign up</Link>
        </nav>
      </div>
      <div className="page-wrap site-footer-bottom"><span>© {new Date().getFullYear()} AutoGrant</span><span>Made for founders finding their next step.</span></div>
    </footer>
  );
}
