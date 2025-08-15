"""
Application configuration settings.

This module handles all configuration management using Pydantic settings
for type safety and validation.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Settings can be overridden via environment variables with the
    prefix specified in the Config class.
    
    Example environment variables:
    - INVENTORY_DATABASE_URL=sqlite:///./custom.db
    - INVENTORY_DATABASE_ECHO=true
    - INVENTORY_HOST=127.0.0.1
    - INVENTORY_PORT=8080
    """
    
    # Database settings
    database_url: str = "sqlite:///./inventory.db"
    database_echo: bool = False  # Set to True for SQL query logging
    database_pool_size: int = 5  # Connection pool size
    database_max_overflow: int = 10  # Max overflow connections
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True  # Auto-reload on code changes (development only)
    
    # API settings
    api_title: str = "Inventory Management API"
    api_version: str = "1.0.0"
    api_description: str = "A RESTful API for managing product inventory with atomic stock operations"
    
    # Environment
    environment: str = "development"  # development, production, testing
    
    class Config:
        env_prefix = "INVENTORY_"
        case_sensitive = False
        env_file = ".env"  # Load from .env file if present


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Using lru_cache ensures settings are loaded only once and reused
    throughout the application lifecycle.
    
    Returns:
        Settings: Application configuration instance
    """
    return Settings()