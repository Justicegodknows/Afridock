from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_env: str = "local"
    api_secret_key: str = "change-me-in-every-environment"
    api_cors_origins: str = "http://localhost:5173"

    database_url: str = "postgresql+asyncpg://afridock:afridock@localhost:5432/afridock"
    redis_url: str = "redis://localhost:6379/0"

    # Fernet key (32 url-safe base64 bytes) used to encrypt provider
    # credentials at rest. Leave unset for local dev — a key is derived
    # from api_secret_key instead; set a real value in every deployed
    # environment (see inference/credentials.py).
    credential_encryption_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
