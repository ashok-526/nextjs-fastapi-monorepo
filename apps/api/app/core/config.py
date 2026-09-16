from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str

    S3_ENDPOINT: str
    S3_BUCKET: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str

    JWT_SECRET: str

    NEXT_PUBLIC_CDN_URL: str
    WEB_ORIGIN: str | None = Field(default=None, alias="NEXT_PUBLIC_API_BASE")

    CORS_ORIGINS: List[str] = Field(default_factory=list, description="Comma-separated list of origins")

    @staticmethod
    def _split_csv(value: str | None) -> list[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    def model_post_init(self, __context: dict) -> None:  # type: ignore[override]
        # Normalize CORS origins from CSV if provided as a single string
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = self._split_csv(self.CORS_ORIGINS)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
