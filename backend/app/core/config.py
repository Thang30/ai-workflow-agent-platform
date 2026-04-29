import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = ".env"


def _default_frontend_origins() -> list[str]:
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-workflow-agent-platform-frontend.vercel.app",
    ]


def _normalize_database_url(value: str) -> str:
    normalized = value.strip()

    if normalized.startswith("postgres://"):
        return normalized.replace("postgres://", "postgresql+psycopg://", 1)

    if normalized.startswith("postgresql://"):
        return normalized.replace("postgresql://", "postgresql+psycopg://", 1)

    return normalized


class DatabaseSettings(BaseSettings):
    database_url: str

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return _normalize_database_url(value)

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


class Settings(DatabaseSettings):
    hf_token: str
    model: str
    tavily_api_key: str | None = None
    self_improvement_low_score_threshold: int = 7
    self_improvement_max_retries: int = 1
    experiment_enabled: bool = False
    experiment_name: str | None = None
    experiment_type: str | None = None
    experiment_variant_a_name: str = "A"
    experiment_variant_b_name: str = "B"
    experiment_variant_a_model: str | None = None
    experiment_variant_b_model: str | None = None
    experiment_variant_a_planner_prompt: str | None = None
    experiment_variant_b_planner_prompt: str | None = None
    experiment_variant_a_planner_prompt_file: str | None = None
    experiment_variant_b_planner_prompt_file: str | None = None
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

    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")


database_settings = DatabaseSettings()
settings = Settings()
