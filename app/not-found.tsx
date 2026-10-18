import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";

export const metadata: Metadata = {
  title: "Page Not Found",
  description: "This AutoGrant page could not be found. Return home or open your grant board."
};

export default function NotFound() {
  return <div className="message-page"><SiteHeader /><main className="message-main not-found-main page-wrap"><div className="not-found-number" aria-hidden="true">404</div><p className="message-kicker">Wrong turn</p><h1>This page went off the map.</h1><p className="message-lead">The link may have moved, or the address may have a typo. Your grant search is still right where you left it.</p><div className="message-actions"><Link className="landing-primary" href="/">Back to home <span aria-hidden="true">↗</span></Link><Link className="landing-secondary" href="/dashboard">Open grant board</Link></div></main><SiteFooter /></div>;
}
