import type { Metadata } from "next";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import AuthForm from "@/components/AuthForm";

export const metadata: Metadata = {
  title: "Create an Account",
  description: "Create your AutoGrant account to discover startup grants, review matches, and prepare application drafts."
};

export default function SignupPage() {
  return <div className="auth-page auth-page-v2"><SiteHeader /><main className="auth-main auth-main-v2 page-wrap"><div className="auth-side auth-side-v2"><div className="auth-side-signal" aria-hidden="true"><span /><span /><span /><i /></div><div className="auth-side-content"><h1>Start with what you’re building.</h1><p>See funding opportunities with their sources and fit in view, then shape your first draft.</p></div><div className="auth-side-bottom">Your story gives the search its direction.</div></div><AuthForm mode="signup" /></main><SiteFooter /></div>;
}
