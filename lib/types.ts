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
