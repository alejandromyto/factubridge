from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    # Base de datos
    database_url: str
    
    # Redis
    redis_url: str
    
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
    aeat_wsdl_url: str
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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()