from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    # Base de datos
    database_url: str = Field(default="", min_length=1)

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Entorno
    env: str = "development"
    debug: bool = True

    # API
    api_prefix: str = "/v1"
    api_title: str = "Verifactu API"
    api_version: str = "1.0.0"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # AEAT
    aeat_wsdl_url: str = Field(default="", min_length=1)
    aeat_timeout: int = 30

    # Certificados (cuando los tengas)
    cert_path: str | None = None
    cert_key_path: str | None = None
    cert_password: str | None = None

    # Webhooks
    webhook_timeout: int = 10
    webhook_max_retries: int = 3

    # Logs
    log_level: str = "INFO"

    # Sentry (opcional)
    sentry_dsn: str | None = None

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @field_validator("database_url", "aeat_wsdl_url")
    @classmethod
    def check_required_urls(cls, v: str) -> str:
        if not v:
            raise ValueError("Este campo es obligatorio en .env")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
