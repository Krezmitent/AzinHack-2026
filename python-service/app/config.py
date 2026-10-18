from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    tinyfish_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    firebase_service_account_json: str = ""
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
