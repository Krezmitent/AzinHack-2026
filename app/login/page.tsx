import type { Metadata } from "next";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import AuthForm from "@/components/AuthForm";

export const metadata: Metadata = {
  title: "Log In",
  description: "Log in to AutoGrant to continue your startup grant search and work on your applications."
};

export default function LoginPage() {
  return <div className="auth-page auth-page-v2"><SiteHeader /><main className="auth-main auth-main-v2 page-wrap"><div className="auth-side auth-side-v2"><div className="auth-side-signal" aria-hidden="true"><span /><span /><span /><i /></div><div className="auth-side-content"><h1>Your funding desk is ready.</h1><p>Return to the opportunities you found and the application drafts you started.</p></div><div className="auth-side-bottom">Search with context. Decide with confidence.</div></div><AuthForm mode="login" /></main><SiteFooter /></div>;
}
