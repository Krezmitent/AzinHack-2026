import BrandLogo from "@/components/BrandLogo";
import Link from "next/link";

export default function SiteFooter() {
  return (
    <footer className="site-footer site-footer-v2">
      <div className="page-wrap site-footer-inner">
        <div className="site-footer-intro">
          <Link className="brand footer-brand" href="/" aria-label="AutoGrant home">
            <BrandLogo />
          </Link>
          <p>A clearer route from discovery to application.</p>
        </div>
        <nav aria-label="Footer navigation">
          <Link href="/#how-it-works">How it works</Link>
          <Link href="/#why-autogrant">The approach</Link>
          <Link href="/dashboard">Grant board</Link>
          <Link href="/login">Log in</Link>
          <Link href="/signup">Create account</Link>
        </nav>
      </div>
      <div className="page-wrap site-footer-bottom"><span>© {new Date().getFullYear()} AutoGrant</span><span>You review every draft before an application run.</span></div>
      <div className="site-footer-signature">
        <div className="page-wrap">
          <Link className="site-footer-signature-link" href="/" aria-label="AutoGrant home">
            <BrandLogo />
          </Link>
        </div>
      </div>
    </footer>
  );
}
