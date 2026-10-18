import type { Grant, StartupProfile } from "./types";
import { firebaseServices } from "./firebase";

export type ApplicationRun = {
  id: string;
  grant_title: string;
  source_url: string;
  application_url: string;
  status: "starting" | "pending" | "submitted" | "not_submitted" | "unknown";
  message: string;
  evidence?: string | null;
  provider_status?: string | null;
  run_id?: string | null;
  created_at: string;
  updated_at: string;
};

function responseError(data: unknown, status: number): string {
  if (data && typeof data === "object" && "detail" in data) {
    const detail = data.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const messages = detail.slice(0, 3).map((issue) => {
        if (!issue || typeof issue !== "object") return "";
        const field = "loc" in issue && Array.isArray(issue.loc) ? issue.loc.slice(1).join(".") : "";
        const message = "msg" in issue && typeof issue.msg === "string" ? issue.msg : "";
        return [field, message].filter(Boolean).join(": ");
      }).filter(Boolean);
      if (messages.length) return `Check these details: ${messages.join("; ")}`;
    }
  }
  return `The grant service returned HTTP ${status}.`;
}

async function request<T>(path: string, body?: unknown, method: "GET" | "POST" = "POST"): Promise<T> {
  const user = firebaseServices().auth.currentUser;
  if (!user) throw new Error("Sign in before using the grant tools.");
  const token = await user.getIdToken();
  const controller = new AbortController();
  const timeoutMs = path === "/api/execute" ? 45_000 : path === "/api/discover" ? 100_000 : method === "GET" ? 35_000 : 70_000;
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(path, {
      method,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: method === "POST" ? JSON.stringify(body) : undefined,
      signal: controller.signal
    });
    const data: unknown = await response.json().catch(() => null);
    if (!response.ok) throw new Error(responseError(data, response.status));
    if (!data || typeof data !== "object") throw new Error("The grant service returned an invalid response.");
    return data as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") throw new Error("The grant service timed out. Please try again.");
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export const discoverGrants = (location: string, sector: string) => request<{ grants: Grant[] }>("/api/discover", { location, sector });
export const scoreGrant = (grant: Grant, profile: StartupProfile) =>
  request<Pick<Grant, "match_score" | "match_reason">>("/api/score", { grant, profile });
export const draftApplication = (grant: Grant, profile: StartupProfile, questions: string[]) =>
  request<{ answers: Record<string, string> }>("/api/draft", { grant, profile, questions });
export const executeApplication = (grant: Grant, answers: Record<string, string>, vaultCredentialLabels: string[]) =>
  request<{ run: ApplicationRun }>("/api/execute", {
    grant,
    drafted_answers: answers,
    vault_credential_labels: vaultCredentialLabels,
    confirm_submit: true
  });
export const listApplicationRuns = () => request<{ runs: ApplicationRun[] }>("/api/application-runs", undefined, "GET");
export const getApplicationRun = (id: string) => {
  if (!/^[a-f0-9]{64}$/.test(id)) throw new Error("Invalid application run ID.");
  return request<{ run: ApplicationRun }>(`/api/application-runs/${id}`, undefined, "GET");
};
