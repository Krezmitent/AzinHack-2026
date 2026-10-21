from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    tinyfish_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    firebase_service_account_json: str = ""
    allowed_origins: str = "http://localhost:3000"
    public_webhook_base_url: str = ""
    max_monitors_per_user: int = Field(default=10, ge=1, le=50)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
