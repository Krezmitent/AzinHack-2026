import type { Metadata } from "next";
import Link from "next/link";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";

export const metadata: Metadata = {
  title: "Thank You",
  description: "Thank you for using AutoGrant. Return to your grant board or explore more about the product.",
  robots: { index: false, follow: false }
};

export default function ThankYouPage() {
  return <div className="message-page message-page-v2"><SiteHeader /><main className="message-main message-main-v2 page-wrap"><div className="message-orbit" aria-hidden="true"><span /><span /><span /></div><div className="message-content"><p className="message-kicker">Your next step</p><h1>Keep the application in view.</h1><p className="message-lead">If you started an application run, check the provider’s portal for its final status. This page does not confirm that the provider received a submission.</p><div className="message-actions"><Link className="landing-primary" href="/dashboard">Open grant board <span aria-hidden="true">↗</span></Link><Link className="landing-secondary" href="/">Go home</Link></div></div></main><SiteFooter /></div>;
}
