import { cert, getApp, getApps, initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";
import { NextResponse } from "next/server";

const ADMIN_APP_NAME = "autogrant-api";
const UPSTREAM_TIMEOUT_MS: Record<string, number> = {
  "/api/discover-grants": 100_000,
  "/api/score-grant": 70_000,
  "/api/draft-application": 70_000,
  "/api/execute-application": 40_000,
  "/api/application-runs": 30_000
};

function adminAuth() {
  const credentials = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (!credentials) throw new Error("Firebase Admin is not configured.");

  const app = getApps().some((candidate) => candidate.name === ADMIN_APP_NAME)
    ? getApp(ADMIN_APP_NAME)
    : initializeApp({ credential: cert(JSON.parse(credentials)) }, ADMIN_APP_NAME);
  return getAuth(app);
}

function bearerToken(request: Request): string | null {
  const header = request.headers.get("authorization");
  const match = header?.match(/^Bearer ([^\s]+)$/i);
  return match?.[1] ?? null;
}

export async function forwardToPython(request: Request, endpoint: string, method: "GET" | "POST" = "POST") {
  const token = bearerToken(request);
  if (!token) return NextResponse.json({ detail: "A Firebase ID token is required." }, { status: 401 });

  try {
    // Check revocation for the endpoint that can initiate an external submission.
    const claims = await adminAuth().verifyIdToken(token, endpoint === "/api/execute-application" || endpoint.startsWith("/api/application-runs"));
    if (!claims.email_verified) return NextResponse.json({ detail: "Verify your email address before using grant tools." }, { status: 403 });
  } catch (error) {
    if (error instanceof SyntaxError || (error instanceof Error && error.message === "Firebase Admin is not configured.")) {
      return NextResponse.json({ detail: "Firebase Admin is not configured." }, { status: 503 });
    }
    const code = typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
    if (["auth/invalid-id-token", "auth/id-token-expired", "auth/id-token-revoked", "auth/user-disabled", "auth/argument-error"].includes(code)) {
      return NextResponse.json({ detail: "Your session is invalid or expired. Please sign in again." }, { status: 401 });
    }
    return NextResponse.json({ detail: "Authentication service is unavailable." }, { status: 503 });
  }

  let body: unknown;
  if (method === "POST") {
    try {
      body = await request.json();
    } catch {
      return NextResponse.json({ detail: "A JSON request body is required." }, { status: 400 });
    }
  }

  const serviceUrl = process.env.PYTHON_SERVICE_URL || (process.env.NODE_ENV === "production" ? "" : "http://localhost:8000");
  if (!serviceUrl) {
    return NextResponse.json({ detail: "Automation service URL is not configured." }, { status: 503 });
  }

  try {
    const response = await fetch(`${serviceUrl}${endpoint}`, {
      method,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: method === "POST" ? JSON.stringify(body) : undefined,
      cache: "no-store",
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS[endpoint] ?? 70_000)
    });
    const data = await response.json().catch(() => ({ detail: "Automation service returned an invalid response." }));
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    if (error instanceof Error && (error.name === "TimeoutError" || error.name === "AbortError")) {
      return NextResponse.json({ detail: "Automation service timed out. Please try again." }, { status: 504 });
    }
    return NextResponse.json({ detail: "Automation service is unavailable." }, { status: 502 });
  }
}
