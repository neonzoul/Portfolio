from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Existing/feature flags
    MAX_KEYS_PER_USER: int = 5

    # JWT settings
    SECRET_KEY: str = "your_super_secret_key_that_should_be_in_a_env_file"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
