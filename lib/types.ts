export type StartupProfile = {
  sector: string;
  revenue: string;
  demographics: string;
  pitchDeckText: string;
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
};
