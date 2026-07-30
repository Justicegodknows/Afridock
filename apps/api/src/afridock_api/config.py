from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_env: str = "local"
    api_secret_key: str = "change-me-in-every-environment"
    api_cors_origins: str = "http://localhost:5173"

    # Cookie SameSite/Secure normally derive from api_env (Lax + non-Secure
    # on plain-http local dev, Secure everywhere else) — see cookie_secure
    # below. Override only when the frontend is genuinely cross-site from
    # the API (e.g. a dev tunnel), which also requires the API itself to be
    # served over HTTPS: browsers drop `Secure` cookies set over plain HTTP,
    # and SameSite=None cookies must be Secure. Flipping this alone with the
    # API still on http://localhost will not make cross-site auth work.
    api_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    api_cookie_secure: bool | None = None

    @property
    def cookie_secure(self) -> bool:
        if self.api_cookie_secure is not None:
            return self.api_cookie_secure
        return self.api_env != "local"

    # App runtime connection — a non-superuser role (afridock_app, created by
    # migration 0002) so Postgres RLS policies actually apply. Postgres
    # superusers and table owners always bypass RLS regardless of
    # ENABLE/FORCE, which is exactly what afridock (migrations_database_url)
    # is, so the app must never query through that connection.
    database_url: str = (
        "postgresql+asyncpg://afridock_app:afridock_app_local_dev@localhost:5432/afridock"
    )
    # Migrations connection — the superuser role, needed to create tables,
    # the afridock_app role itself, and grants. Alembic (alembic/env.py) is
    # the only thing that should ever use this.
    migrations_database_url: str = "postgresql+asyncpg://afridock:afridock@localhost:5432/afridock"
    redis_url: str = "redis://localhost:6379/0"

    # Fernet key (32 url-safe base64 bytes) used to encrypt provider
    # credentials at rest. Leave unset for local dev — a key is derived
    # from api_secret_key instead; set a real value in every deployed
    # environment (see inference/credentials.py).
    credential_encryption_key: str = ""

    # Real LLM provider credentials (per §2.4 of the plan). Leave all blank
    # for local-dev "stub mode" (see inference/client.py) — chat still works
    # end to end with a canned streamed response, no secrets required.
    huggingface_api_token: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Self-hosted NVIDIA NIM instance (e.g. a DGX Spark box running an
    # OpenAI-compatible NIM microservice) — per-deployment network address,
    # so unlike Ollama's fixed Docker Compose service name this can't be
    # hardcoded in profiles.yaml; resolved dynamically in inference/client.py.
    # Zero marginal per-token cost (your own hardware), so this is treated as
    # self-hosted/free per CLAUDE.md's #1 constraint, not commercial.
    nvidia_nim_api_key: str = ""
    nvidia_nim_base_url: str = ""

    # NVIDIA's *hosted* API catalog (https://integrate.api.nvidia.com/v1) —
    # a distinct credential from the self-hosted NIM box above: this is
    # NVIDIA's own paid cloud infrastructure serving open-weight models
    # (e.g. meta/llama-3.3-70b-instruct), not your hardware. Priced $0 in
    # profiles.yaml for consistency with this registry's existing
    # Hugging-Face-hosted entries (same "open-weight model via a hosted API"
    # treatment), not because it's guaranteed free at any volume.
    nvidia_api_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
