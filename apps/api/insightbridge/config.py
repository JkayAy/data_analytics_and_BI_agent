from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILES = (
    _ROOT / ".env",
    Path(".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(p) for p in _ENV_FILES if p.exists()] or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql://insight:insight@localhost:5432/insightbridge"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    cors_origins: str = "http://localhost:3000"
    query_row_limit: int = 10_000
    query_timeout_seconds: int = 30
    api_key: str | None = None
    multi_agent_use_langgraph: bool = True
    conversation_history_turns: int = 6
    investigation_max_queries: int = 5
    investigation_budget_ms: int = 120_000
    semantic_layer_path: Path | None = None

    auth_required: bool = False
    jwt_secret: str = "dev-change-me-in-production"
    jwt_expire_hours: int = 24
    encryption_key: str | None = None
    magic_link_expire_minutes: int = 15
    magic_link_dev_expose: bool = True
    default_org_id: str = "00000000-0000-4000-a000-000000000001"
    default_user_id: str = "00000000-0000-4000-a000-000000000002"
    monthly_query_cap: int = 0
    scheduler_enabled: bool = True
    scheduler_poll_seconds: int = 60
    slack_signing_secret: str | None = None

    def resolved_semantic_layer_path(self) -> Path:
        import os

        env_path = os.environ.get("SEMANTIC_LAYER_PATH")
        if env_path:
            return Path(env_path)
        if self.semantic_layer_path:
            return self.semantic_layer_path
        return _ROOT / "packages" / "semantic-layer" / "metrics.yaml"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
