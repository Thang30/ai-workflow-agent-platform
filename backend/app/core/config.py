import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_frontend_origins() -> list[str]:
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-workflow-agent-platform-frontend.vercel.app",
    ]


class Settings(BaseSettings):
    hf_token: str
    model: str
    tavily_api_key: str | None = None
    frontend_origins: list[str] = Field(default_factory=_default_frontend_origins)
    frontend_origin_regex: str = (
        r"https://ai-workflow-agent-platform-frontend(?:-[a-z0-9-]+)?\.vercel\.app"
    )

    @field_validator("frontend_origins", mode="before")
    @classmethod
    def parse_frontend_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None:
            return _default_frontend_origins()

        if isinstance(value, str):
            stripped_value = value.strip()

            if not stripped_value:
                return []

            try:
                parsed_value = json.loads(stripped_value)
            except json.JSONDecodeError:
                return [
                    origin.strip()
                    for origin in stripped_value.split(",")
                    if origin.strip()
                ]

            if isinstance(parsed_value, str):
                return [parsed_value]

            if isinstance(parsed_value, list):
                return [
                    str(origin).strip()
                    for origin in parsed_value
                    if str(origin).strip()
                ]

        return value

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
