import type { Metadata } from "next";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import AuthForm from "@/components/AuthForm";

export const metadata: Metadata = {
  title: "Log In",
  description: "Log in to AutoGrant to continue your startup grant search and work on your applications."
};

export default function LoginPage() {
  return <div className="auth-page"><SiteHeader /><main className="auth-main page-wrap"><div className="auth-side"><span className="auth-side-mark">✳</span><h1>Your next opportunity is waiting.</h1><p>Return to your funding desk and keep building a shortlist that fits your startup.</p><div className="auth-side-bottom">Search thoughtfully. Apply confidently.</div></div><AuthForm mode="login" /></main><SiteFooter /></div>;
}
