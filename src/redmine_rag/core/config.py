from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        enable_decoding=False,
    )

    app_env: str = "dev"
    app_name: str = "redmine-rag"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./data/redmine_rag.db"
    vector_index_path: str = "./indexes/chunks.index"
    vector_meta_path: str = "./indexes/chunks.meta.json"
    embedding_dim: int = 256
    retrieval_lexical_weight: float = 0.65
    retrieval_vector_weight: float = 0.35
    retrieval_rrf_k: int = 60
    retrieval_candidate_multiplier: int = 4

    redmine_base_url: str = "https://redmine.example.com"
    redmine_api_key: str = "replace_me"
    redmine_project_ids: list[int] = Field(default_factory=list)
    redmine_modules: list[str] = Field(
        default_factory=lambda: [
            "projects",
            "users",
            "groups",
            "trackers",
            "issue_statuses",
            "issue_priorities",
            "issues",
            "time_entries",
            "news",
            "documents",
            "files",
            "boards",
            "wiki",
        ]
    )
    redmine_board_ids: list[int] = Field(default_factory=list)
    redmine_wiki_pages: list[str] = Field(default_factory=list)
    redmine_verify_ssl: bool = True
    sync_overlap_minutes: int = 15

    llm_provider: str = "api"
    llm_model: str = "gpt-5-mini"

    @field_validator("redmine_project_ids", mode="before")
    @classmethod
    def parse_project_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        raise ValueError("Invalid REDMINE_PROJECT_IDS value")

    @field_validator("redmine_board_ids", mode="before")
    @classmethod
    def parse_board_ids(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(item) for item in value]
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        raise ValueError("Invalid REDMINE_BOARD_IDS value")

    @field_validator("redmine_modules", mode="before")
    @classmethod
    def parse_modules(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(item).strip().lower() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        raise ValueError("Invalid REDMINE_MODULES value")

    @field_validator("redmine_wiki_pages", mode="before")
    @classmethod
    def parse_wiki_pages(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        raise ValueError("Invalid REDMINE_WIKI_PAGES value")

    @field_validator("embedding_dim", "retrieval_rrf_k", "retrieval_candidate_multiplier")
    @classmethod
    def validate_positive_ints(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("Value must be > 0")
        return value

    @field_validator("retrieval_lexical_weight", "retrieval_vector_weight")
    @classmethod
    def validate_weights(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Weight must be >= 0")
        return value

    @property
    def data_dir(self) -> Path:
        return Path("data")

    @property
    def index_dir(self) -> Path:
        return Path("indexes")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    return settings
