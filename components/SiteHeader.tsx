import BrandLogo from "@/components/BrandLogo";
import Link from "next/link";
import "@/app/chrome-redesign.css";

export default function SiteHeader() {
  return (
    <header className="site-header site-header-v2 page-wrap">
      <Link className="brand" href="/" aria-label="AutoGrant home">
        <BrandLogo />
      </Link>
      <nav className="site-nav site-nav-v2" aria-label="Main navigation">
        <Link href="/#how-it-works">How it works</Link>
        <Link href="/#why-autogrant">The approach</Link>
        <Link href="/dashboard">Funding desk</Link>
      </nav>
      <div className="site-header-actions site-header-actions-v2">
        <Link className="site-login" href="/login">Log in</Link>
        <Link className="site-signup" href="/signup">Get started <span aria-hidden="true">↗</span></Link>
      </div>
      <details className="site-menu">
        <summary aria-label="Open navigation menu"><span>Menu</span><i aria-hidden="true"><span /><span /></i></summary>
        <nav aria-label="Mobile navigation">
          <Link href="/#how-it-works">How it works</Link>
          <Link href="/#why-autogrant">The approach</Link>
          <Link href="/dashboard">Funding desk</Link>
          <Link href="/login">Log in</Link>
          <Link href="/signup">Create account</Link>
        </nav>
      </details>
    </header>
  );
}
