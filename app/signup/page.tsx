import type { Metadata } from "next";
import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import AuthForm from "@/components/AuthForm";

export const metadata: Metadata = {
  title: "Create an Account",
  description: "Create your AutoGrant account to discover startup grants, review matches, and prepare application drafts."
};

export default function SignupPage() {
  return <div className="auth-page"><SiteHeader /><main className="auth-main page-wrap"><div className="auth-side"><span className="auth-side-mark">✳</span><h1>Make room for the right grant.</h1><p>Start with your story. We’ll help turn it into a sharper search and a stronger first draft.</p><div className="auth-side-bottom">Built around your startup.</div></div><AuthForm mode="signup" /></main><SiteFooter /></div>;
}
