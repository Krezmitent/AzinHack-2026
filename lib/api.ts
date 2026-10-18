import type { Grant, StartupProfile } from "./types";

async function request<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const data = await response.json().catch(() => ({ detail: "The server returned an invalid response." }));
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data as T;
}

export const discoverGrants = () => request<{ grants: Grant[] }>("/api/discover", {});
export const scoreGrant = (grant: Grant, profile: StartupProfile) =>
  request<Pick<Grant, "match_score" | "match_reason">>("/api/score", { grant, profile });
export const draftApplication = (grant: Grant, profile: StartupProfile, questions: string[]) =>
  request<{ answers: Record<string, string> }>("/api/draft", { grant, profile, questions });
export const executeApplication = (grant: Grant, answers: Record<string, string>, vaultCredentialLabels: string[]) =>
  request<{ run: unknown }>("/api/execute", {
    grant,
    drafted_answers: answers,
    vault_credential_labels: vaultCredentialLabels,
    confirm_submit: true
  });
