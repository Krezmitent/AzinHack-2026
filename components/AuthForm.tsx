"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createUserWithEmailAndPassword, sendEmailVerification, sendPasswordResetEmail, signInWithEmailAndPassword, signOut, updateProfile } from "firebase/auth";
import { firebaseServices } from "@/lib/firebase";

type Mode = "login" | "signup";

function readableAuthError(error: unknown): string {
  const code = typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
  switch (code) {
    case "auth/invalid-email": return "Enter a valid email address.";
    case "auth/invalid-credential":
    case "auth/user-not-found":
    case "auth/wrong-password": return "The email or password is incorrect.";
    case "auth/email-already-in-use": return "An account already uses this email. Log in instead.";
    case "auth/weak-password": return "Choose a password with at least six characters.";
    case "auth/operation-not-allowed": return "Email and password sign-in is not enabled in Firebase yet.";
    case "auth/network-request-failed": return "Could not reach Firebase. Check your connection and try again.";
    case "auth/too-many-requests": return "Too many attempts. Wait a little before trying again.";
    default: return error instanceof Error ? error.message : "Something went wrong. Try again.";
  }
}

export default function AuthForm({ mode }: { mode: Mode }) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ text: string; tone: "error" | "success" } | null>(null);
  const isSignup = mode === "signup";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isSignup && password !== confirmPassword) {
      setMessage({ text: "The passwords do not match.", tone: "error" });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const { auth } = firebaseServices();
      if (isSignup) {
        const { user } = await createUserWithEmailAndPassword(auth, email.trim(), password);
        if (name.trim()) await updateProfile(user, { displayName: name.trim() }).catch(() => undefined);
        try {
          await sendEmailVerification(user);
          setMessage({ text: "Account created. Check your inbox to verify your email, then log in.", tone: "success" });
        } catch (error) {
          setMessage({ text: `Account created, but the verification email could not be sent. Log in to retry. ${readableAuthError(error)}`, tone: "error" });
        }
        await signOut(auth);
        return;
      } else {
        const { user } = await signInWithEmailAndPassword(auth, email.trim(), password);
        if (!user.emailVerified) {
          try {
            await sendEmailVerification(user);
            setMessage({ text: "Verify your email before continuing. We sent a new link to your inbox.", tone: "success" });
          } catch (error) {
            setMessage({ text: `Verify your email before continuing. We could not resend the link: ${readableAuthError(error)}`, tone: "error" });
          }
          await signOut(auth);
          return;
        }
      }
      router.push("/dashboard");
      router.refresh();
    } catch (error) {
      setMessage({ text: readableAuthError(error), tone: "error" });
    } finally { setBusy(false); }
  }

  async function resetPassword() {
    if (!email.trim()) {
      setMessage({ text: "Enter your email above, then choose Reset password.", tone: "error" });
      return;
    }
    setBusy(true);
    setMessage(null);
    try {
      const { auth } = firebaseServices();
      await sendPasswordResetEmail(auth, email.trim());
      setMessage({ text: "If this email has an account, a reset link is on its way.", tone: "success" });
    } catch (error) {
      setMessage({ text: readableAuthError(error), tone: "error" });
    } finally { setBusy(false); }
  }

  return (
    <div className="auth-card auth-card-v2">
      <div className="auth-card-heading"><h2>{isSignup ? "Create your account" : "Welcome back"}</h2><p>{isSignup ? "Create an account, verify your email, and start a funding shortlist shaped by your startup." : "Sign in to continue your shortlist and application drafts."}</p></div>
      <form className="auth-form" onSubmit={submit}>
        {isSignup && <div className="field"><label htmlFor="auth-name">Your name <span className="optional">Optional</span></label><input id="auth-name" autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder="How should we call you?" /></div>}
        <div className="field"><label htmlFor="auth-email">Email address</label><input id="auth-email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@startup.com" /></div>
        <div className="field"><div className="auth-label-row"><label htmlFor="auth-password">Password</label>{!isSignup && <button type="button" className="text-button" onClick={resetPassword} disabled={busy}>Reset password</button>}</div><input id="auth-password" type="password" autoComplete={isSignup ? "new-password" : "current-password"} minLength={6} required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 6 characters" /></div>
        {isSignup && <div className="field"><label htmlFor="auth-confirm">Confirm password</label><input id="auth-confirm" type="password" autoComplete="new-password" minLength={6} required value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="Enter your password again" /></div>}
        {message && <div className={`auth-message auth-message-${message.tone}`} role="status" aria-live="polite">{message.text}</div>}
        <button className="auth-submit" type="submit" disabled={busy}>{busy ? "Please wait…" : isSignup ? "Create account" : "Log in"}<span aria-hidden="true">↗</span></button>
      </form>
      <p className="auth-switch">{isSignup ? "Already have an account?" : "New to AutoGrant?"} <Link href={isSignup ? "/login" : "/signup"}>{isSignup ? "Log in" : "Create an account"}</Link></p>
    </div>
  );
}
