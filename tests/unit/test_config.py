"""Test configuration and settings."""

import pytest
from app.config import Settings, Secrets


def test_development_database_url():
    """Test development database URL configuration."""
    secrets = Secrets(
        secret_key="test-key", file_storage_path="./test_files", max_file_size_mb=10
    )
    settings = Settings(app_env="development", secrets=secrets)

    assert settings.database_url == "sqlite:///./dev.db"
    assert settings.is_development is True
    assert settings.is_production is False


def test_production_database_url():
    """Test production database URL configuration."""
    secrets = Secrets(
        secret_key="test-key",
        file_storage_path="./test_files",
        max_file_size_mb=10,
        database_url_prod="postgresql://user:pass@localhost/db",
    )
    settings = Settings(app_env="production", secrets=secrets)

    assert settings.database_url == "postgresql://user:pass@localhost/db"
    assert settings.is_development is False
    assert settings.is_production is True
