export type StartupProfile = {
  sector: string;
  location: string;
  revenue: string;
  demographics: string;
  pitchDeckText: string;
  companyFacts?: string;
};

export type Grant = {
  id?: string;
  title: string;
  source_url: string;
  application_url?: string;
  eligibility_criteria: string[];
  clean_markdown: string;
  match_score?: number;
  match_reason?: string;
  eligibility_checks?: { criterion: string; status: "met" | "unmet" | "unknown"; reason: string }[];
  source_version?: string;
  checked_at?: string;
  assessment_profile?: string;
  inspection?: {
    access: "public" | "login_required" | "manual_review" | "unavailable";
    complete: boolean;
    explanation: string;
    provider: string;
    round_name: string;
    amount: string;
    deadline_date: string;
    application_url: string;
    eligibility_criteria: string[];
    required_documents: string[];
    questions: ApplicationQuestion[];
    evidence: { field: string; value: string; quote: string; source_url: string }[];
  } | null;
};

export type ApplicationQuestion = {
  label: string;
  field_type: "text" | "textarea" | "email" | "number" | "date" | "select" | "checkbox" | "file" | "other";
  required: boolean;
  max_words: number;
  max_characters: number;
  options: string[];
  help_text: string;
};

export type InspectionRun = {
  id: string;
  generation?: string;
  status: "not_started" | "starting" | "pending" | "completed" | "failed" | "unknown" | "stale";
  message?: string;
  run_id?: string;
  streaming_url?: string | null;
};

export type SavedDraft = {
  opportunity_id: string;
  answers: Record<string, string>;
  revision: number;
  source_version: string;
  profile: StartupProfile;
  updated_at: string;
};

export type FundingWatch = {
  id: string; type: "fetch" | "search"; target: string; opportunity_id?: string; name: string;
  cadence: "daily" | "six_hourly"; timezone: string; purpose: string;
  status: string; monitor_id?: string | null; last_error?: string; last_checked_at?: string | null;
  check_status?: string | null; created_at: string;
};
export type FundingEvent = {
  id: string; kind: string; title: string; message: string; created_at: string; read: boolean;
  source_url?: string; opportunity_id?: string; requires_review?: boolean; changed_fields?: string[];
  quotes?: { field: string; before: string; after: string; quote: string }[];
};
export type TrackedApplication = {
  id: string; grant_title: string; source_url: string; application_url: string;
  status: "draft" | "submitted" | "under_review" | "information_requested" | "awarded" | "rejected" | "withdrawn";
  status_source?: string; note: string; revision: number; deadline_date?: string; timezone: string;
  updated_at: string; reminder_sent_for?: string;
};
export type FundingRadarData = { watches: FundingWatch[]; events: FundingEvent[]; applications: TrackedApplication[] };
