from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
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
    retrieval_planner_enabled: bool = False
    retrieval_planner_max_expansions: int = 3
    retrieval_planner_timeout_s: float = 12.0
    ask_answer_mode: str = "deterministic"
    ask_llm_timeout_s: float = 20.0
    ask_llm_max_claims: int = 5
    ask_llm_max_retries: int = 1
    ask_llm_cost_limit_usd: float = 0.05

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
    redmine_http_timeout_s: float = 30.0
    redmine_allowed_hosts: list[str] = Field(default_factory=list)
    sync_overlap_minutes: int = 15
    sync_job_history_limit: int = 100

    llm_provider: str = "api"
    llm_model: str = "gpt-5-mini"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "mistral:7b-instruct-v0.3-q4_K_M"
    ollama_timeout_s: float = 45.0
    ollama_max_concurrency: int = 2
    llm_extract_enabled: bool = False
    llm_extract_max_retries: int = 2
    llm_extract_batch_size: int = 20
    llm_extract_max_context_chars: int = 6000
    llm_extract_timeout_s: float = 20.0
    llm_extract_cost_limit_usd: float = 1.0
    llm_runtime_cost_limit_usd: float = 10.0
    llm_circuit_breaker_enabled: bool = True
    llm_circuit_failure_threshold: int = 3
    llm_circuit_slow_threshold_ms: int = 15000
    llm_circuit_slow_threshold_hits: int = 3
    llm_circuit_open_seconds: float = 60.0
    llm_telemetry_latency_window: int = 200
    llm_slo_min_success_rate: float = 0.9
    llm_slo_p95_latency_ms: int = 12000

    @field_validator("app_env")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        return value.strip().lower()

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

    @field_validator("redmine_allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value: object) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [str(item).strip().lower() for item in value if str(item).strip()]
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        raise ValueError("Invalid REDMINE_ALLOWED_HOSTS value")

    @field_validator(
        "embedding_dim",
        "retrieval_rrf_k",
        "retrieval_candidate_multiplier",
        "retrieval_planner_max_expansions",
        "ask_llm_max_claims",
        "ask_llm_max_retries",
        "llm_extract_max_retries",
        "llm_extract_batch_size",
        "llm_extract_max_context_chars",
        "sync_job_history_limit",
        "ollama_max_concurrency",
        "llm_circuit_failure_threshold",
        "llm_circuit_slow_threshold_ms",
        "llm_circuit_slow_threshold_hits",
        "llm_telemetry_latency_window",
        "llm_slo_p95_latency_ms",
    )
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

    @field_validator(
        "llm_extract_timeout_s",
        "llm_extract_cost_limit_usd",
        "ask_llm_cost_limit_usd",
        "llm_runtime_cost_limit_usd",
        "llm_circuit_open_seconds",
        "redmine_http_timeout_s",
        "ollama_timeout_s",
        "ask_llm_timeout_s",
        "retrieval_planner_timeout_s",
    )
    @classmethod
    def validate_non_negative_floats(cls, value: float) -> float:
        if value < 0:
            raise ValueError("Value must be >= 0")
        return value

    @field_validator("llm_slo_min_success_rate")
    @classmethod
    def validate_rate_between_zero_and_one(cls, value: float) -> float:
        if value < 0 or value > 1:
            raise ValueError("Value must be between 0 and 1")
        return value

    @field_validator("ask_answer_mode")
    @classmethod
    def validate_ask_answer_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"deterministic", "llm_grounded"}:
            raise ValueError("ASK_ANSWER_MODE must be one of: deterministic, llm_grounded")
        return normalized

    @field_validator("redmine_api_key")
    @classmethod
    def validate_redmine_api_key(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("REDMINE_API_KEY must not be empty")
        return value

    @field_validator("redmine_base_url")
    @classmethod
    def validate_redmine_base_url(cls, value: str) -> str:
        parsed = urlparse(value.strip())
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("REDMINE_BASE_URL must be absolute URL")
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("REDMINE_BASE_URL must use http or https")
        return value.strip()

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, value: str) -> str:
        parsed = urlparse(value.strip())
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("OLLAMA_BASE_URL must be absolute URL")
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("OLLAMA_BASE_URL must use http or https")
        return value.strip()

    @field_validator("ollama_model")
    @classmethod
    def validate_ollama_model(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("OLLAMA_MODEL must not be empty")
        return value.strip()

    @property
    def data_dir(self) -> Path:
        return Path("data")

    @property
    def index_dir(self) -> Path:
        return Path("indexes")

    @model_validator(mode="after")
    def validate_production_security(self) -> Settings:
        if self.app_env in {"prod", "production"}:
            if self.redmine_api_key.strip() in {"replace_me", "changeme", "test", "mock-api-key"}:
                raise ValueError("In production set non-placeholder REDMINE_API_KEY")
            if not self.redmine_allowed_hosts:
                raise ValueError("In production set REDMINE_ALLOWED_HOSTS outbound allowlist")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    return settings
