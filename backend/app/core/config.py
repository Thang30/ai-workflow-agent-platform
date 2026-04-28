from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    hf_token: str
    model: str
    tavily_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
