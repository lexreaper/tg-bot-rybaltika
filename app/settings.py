from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    demo_mode: bool = False
    demo_database_url: str = 'sqlite+aiosqlite:///./demo.db'
    cors_origins: list[str] = []
    content_admin_token: SecretStr | None = Field(default=None, min_length=24)


@lru_cache
def get_app_settings() -> AppSettings:
    return AppSettings()
