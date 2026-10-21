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
};

export type SavedDraft = {
  opportunity_id: string;
  answers: Record<string, string>;
  revision: number;
  source_version: string;
  profile: StartupProfile;
  updated_at: string;
};
