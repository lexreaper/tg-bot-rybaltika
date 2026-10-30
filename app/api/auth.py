import hmac
from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AdminSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    admin_api_token: SecretStr | None = None

    @field_validator("admin_api_token")
    @classmethod
    def validate_token_length(cls, token: SecretStr | None) -> SecretStr | None:
        if token is not None and len(token.get_secret_value()) < 32:
            raise ValueError("ADMIN_API_TOKEN must contain at least 32 characters")
        return token


@lru_cache
def get_admin_settings() -> AdminSettings:
    return AdminSettings()


bearer_scheme = HTTPBearer(auto_error=False)


async def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> None:
    try:
        expected_token = get_admin_settings().admin_api_token
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication configuration is invalid",
        ) from exc
    if expected_token is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured",
        )
    if credentials is None or not hmac.compare_digest(
        credentials.credentials.encode("utf-8"),
        expected_token.get_secret_value().encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
