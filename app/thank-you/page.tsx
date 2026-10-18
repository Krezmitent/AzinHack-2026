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
  return <div className="message-page"><SiteHeader /><main className="message-main page-wrap"><div className="message-mark" aria-hidden="true">✳</div><p className="message-kicker">Thank you</p><h1>Thanks for taking the next step.</h1><p className="message-lead">If you just started an application run, check the grant portal for its final status. This page does not confirm that the grant provider received a submission.</p><div className="message-actions"><Link className="landing-primary" href="/dashboard">Back to grant board <span aria-hidden="true">↗</span></Link><Link className="landing-secondary" href="/">Go home</Link></div></main><SiteFooter /></div>;
}
