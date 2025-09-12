from dataclasses import dataclass
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Secrets(BaseSettings):
    database_url_prod: str | None = None
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")
    # jwt
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    #   File torage
    file_storage_path: str
    max_file_size_mb: int


@dataclass
class Settings:
    app_env: str
    secrets: Secrets

    @property
    def database_url(self) -> str:
        if self.app_env == "production":
            if not self.secrets.database_url_prod:
                raise RuntimeError(
                    "❌ DATABASE_URL_PROD musi być ustawione w .env lub ENV!"
                )
            return self.secrets.database_url_prod
        elif self.app_env == "development":
            return "sqlite:///./dev.db"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


secrets = Secrets()

settings = Settings(app_env="development", secrets=secrets)
