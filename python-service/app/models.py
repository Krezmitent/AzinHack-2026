from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator
from datetime import date


Location = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Sector = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class StartupProfile(BaseModel):
    sector: Sector
    location: Location
    revenue: str = Field(min_length=1, max_length=120)
    demographics: str = Field(max_length=2_000)
    pitchDeckText: str = Field(min_length=20, max_length=100_000)
    companyFacts: str = Field(default="", max_length=4_000)


class EligibilityCheck(BaseModel):
    criterion: str = Field(min_length=1, max_length=500)
    status: Literal["met", "unmet", "unknown"]
    reason: str = Field(min_length=1, max_length=1000)


class Assessment(BaseModel):
    match_score: int = Field(ge=0, le=100, strict=True)
    match_reason: str = Field(min_length=1, max_length=1000)
    eligibility_checks: list[EligibilityCheck] = Field(default_factory=list, max_length=30)


class ApplicationQuestion(BaseModel):
    label: str = Field(min_length=1, max_length=500)
    field_type: Literal["text", "textarea", "email", "number", "date", "select", "checkbox", "file", "other"]
    required: bool = True
    max_words: int = Field(default=0, ge=0, le=10000)
    max_characters: int = Field(default=0, ge=0, le=100000)
    options: list[str] = Field(default_factory=list, max_length=100)
    help_text: str = Field(default="", max_length=2000)


class SourceFact(BaseModel):
    field: str = Field(min_length=1, max_length=120)
    value: str = Field(min_length=1, max_length=2000)
    quote: str = Field(min_length=1, max_length=2000)
    source_url: str = Field(min_length=1, max_length=2048)


class InspectionResult(BaseModel):
    access: Literal["public", "login_required", "manual_review", "unavailable"]
    complete: bool
    explanation: str = Field(min_length=1, max_length=2000)
    provider: str = Field(default="", max_length=300)
    round_name: str = Field(default="", max_length=300)
    amount: str = Field(default="", max_length=300)
    deadline_date: str = Field(default="", max_length=10)
    application_url: str = Field(default="", max_length=2048)
    eligibility_criteria: list[str] = Field(default_factory=list, max_length=20)
    required_documents: list[str] = Field(default_factory=list, max_length=30)
    questions: list[ApplicationQuestion] = Field(default_factory=list, max_length=20)
    evidence: list[SourceFact] = Field(default_factory=list, max_length=50)

    @field_validator("deadline_date")
    @classmethod
    def valid_deadline(cls, value):
        if value:
            date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def consistent_form(self):
        labels = [question.label for question in self.questions]
        if len(set(labels)) != len(labels):
            raise ValueError("Repeated form labels need manual review.")
        if self.complete and (self.access != "public" or not self.questions or not self.evidence):
            raise ValueError("A complete inspection needs a public form, questions and source evidence.")
        return self


class Grant(BaseModel):
    id: str | None = None
    title: str = Field(min_length=1, max_length=300)
    source_url: str = Field(min_length=1, max_length=2_048)
    application_url: str | None = Field(default=None, max_length=2_048)
    eligibility_criteria: list[str] = Field(default_factory=list, max_length=20)
    clean_markdown: str = Field(default="", max_length=250_000)
    match_score: int | None = None
    match_reason: str | None = None
    eligibility_checks: list[EligibilityCheck] = Field(default_factory=list, max_length=30)
    source_version: str | None = None
    checked_at: str | None = None
    inspection: InspectionResult | None = None


class DiscoverGrantsRequest(BaseModel):
    location: Location
    sector: Sector


class ScoreGrantRequest(BaseModel):
    grant: Grant
    profile: StartupProfile | None = None
    user_id: str | None = None


class DraftApplicationRequest(BaseModel):
    grant: Grant
    profile: StartupProfile | None = None
    user_id: str | None = None
    questions: list[str] = Field(min_length=1, max_length=20)

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, questions: list[str]) -> list[str]:
        if any(not question.strip() or len(question) > 500 for question in questions):
            raise ValueError("Questions must be nonblank and at most 500 characters.")
        return questions


class ExecuteApplicationRequest(BaseModel):
    grant: Grant
    drafted_answers: dict[str, str] = Field(min_length=1, max_length=20)
    vault_credential_labels: list[str] = Field(default_factory=list, max_length=5)
    confirm_submit: bool = False
    draft_revision: int | None = Field(default=None, ge=1)

    @field_validator("drafted_answers")
    @classmethod
    def validate_answers(cls, answers: dict[str, str]) -> dict[str, str]:
        if any(not question.strip() or len(question) > 500 or not answer.strip() or len(answer) > 10_000
               for question, answer in answers.items()):
            raise ValueError("Each question and answer must be nonblank and within the size limit.")
        return answers

    @field_validator("vault_credential_labels")
    @classmethod
    def validate_labels(cls, labels: list[str]) -> list[str]:
        if any(not label.strip() or len(label) > 100 for label in labels):
            raise ValueError("Credential labels must be nonblank and at most 100 characters.")
        return labels
