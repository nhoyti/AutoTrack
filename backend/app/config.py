"""Application configuration for AutoTrack."""

import os
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Configuration settings loaded from environment variables."""

    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "AutoTrack"
    BACKEND_CORS_ORIGINS: list = []

    # Supabase Configuration
    SUPABASE_URL: str = Field(default="", env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(default="", env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(default="", env="SUPABASE_SERVICE_ROLE_KEY")

    # Authentication
    AUTH_SECRET_KEY: str = Field(default="", env="AUTH_SECRET_KEY")
    DEMO_PASSWORD: str = Field(default="autotrack-demo", env="DEMO_PASSWORD")

    # Database
    DATABASE_URL: str = Field(default="", env="DATABASE_URL")

    # Application Settings
    SHOP_TIMEZONE: str = Field(default="UTC", env="SHOP_TIMEZONE")
    FRONTEND_URL: str = Field(default="http://localhost:4200", env="FRONTEND_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    """Get the application settings instance."""
    return settings
