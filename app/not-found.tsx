import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";

export const metadata: Metadata = {
  title: "Page Not Found",
  description: "This AutoGrant page could not be found. Return home or open your grant board."
};

export default function NotFound() {
  return <div className="message-page message-page-v2"><SiteHeader /><main className="message-main message-main-v2 not-found-main page-wrap"><div className="message-orbit message-orbit-missing" aria-hidden="true"><span /><span /><span /><b>404</b></div><div className="message-content"><p className="message-kicker">Page not found</p><h1>This route ends here.</h1><p className="message-lead">Check the address, or head back to your funding desk.</p><div className="message-actions"><Link className="landing-primary" href="/">Go home <span aria-hidden="true">↗</span></Link><Link className="landing-secondary" href="/dashboard">Open grant board</Link></div></div></main><SiteFooter /></div>;
}
