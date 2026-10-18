from pydantic import BaseModel, Field, HttpUrl


class StartupProfile(BaseModel):
    sector: str
    revenue: str
    demographics: str
    pitchDeckText: str = Field(min_length=20, max_length=100_000)


class Grant(BaseModel):
    id: str | None = None
    title: str
    source_url: str
    application_url: str | None = None
    eligibility_criteria: list[str] = []
    clean_markdown: str = ""
    match_score: int | None = None
    match_reason: str | None = None


class ScoreGrantRequest(BaseModel):
    grant: Grant
    profile: StartupProfile | None = None
    user_id: str | None = None


class DraftApplicationRequest(BaseModel):
    grant: Grant
    profile: StartupProfile | None = None
    user_id: str | None = None
    questions: list[str] = Field(min_length=1, max_length=20)


class ExecuteApplicationRequest(BaseModel):
    grant: Grant
    drafted_answers: dict[str, str] = Field(min_length=1)
    vault_credential_labels: list[str] = Field(default_factory=list, max_length=5)
    confirm_submit: bool = False
