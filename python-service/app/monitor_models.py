from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator


def timezone_name(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Choose a valid IANA time zone.") from error
    if any(character.isspace() for character in value):
        raise ValueError("Invalid time zone.")
    return value


class WatchRequest(BaseModel):
    type: Literal["fetch", "search"]
    opportunity_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    query: str = Field(default="", max_length=2000)
    cadence: Literal["daily", "six_hourly"] = "daily"
    timezone: str = Field(default="UTC", max_length=80)
    purpose: str = Field(default="Funding opens or closes, or deadlines, eligibility, award amounts or application requirements change. Ignore navigation, styling and unrelated news.", min_length=1, max_length=2000)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        return timezone_name(value)


class WatchAction(BaseModel):
    action: Literal["pause", "resume", "delete", "check", "sync"]


class ApplicationUpdate(BaseModel):
    status: Literal["draft", "submitted", "under_review", "information_requested", "awarded", "rejected", "withdrawn"] = "draft"
    note: str = Field(default="", max_length=2000)
    expected_revision: int = Field(default=0, ge=0)
    timezone: str = Field(default="UTC", max_length=80)

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value):
        return timezone_name(value)
