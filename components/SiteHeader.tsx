import Link from "next/link";

export default function SiteHeader() {
  return (
    <header className="site-header page-wrap">
      <Link className="brand" href="/" aria-label="AutoGrant home">
        <span className="brand-mark" aria-hidden="true"><span /><span /><span /><span /></span>
        <span>AutoGrant<span className="brand-period">.</span></span>
      </Link>
      <nav className="site-nav" aria-label="Main navigation">
        <Link href="/#how-it-works">How it works</Link>
        <Link href="/#why-autogrant">Why AutoGrant</Link>
        <Link href="/#reviews">Reviews</Link>
      </nav>
      <div className="site-header-actions">
        <Link className="site-login" href="/login">Log in</Link>
        <Link className="site-signup" href="/signup">Get started <span aria-hidden="true">↗</span></Link>
      </div>
    </header>
  );
}
