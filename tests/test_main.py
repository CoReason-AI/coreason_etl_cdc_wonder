# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder


import pytest
from pydantic import ValidationError

from coreason_etl_cdc_wonder.main import hello_world, setup_config


def test_hello_world() -> None:
    assert hello_world() == "Hello World!"


def test_setup_config_default_success() -> None:
    """Test that setup_config successfully initializes default config."""
    app_config, pipeline_config = setup_config()

    # Assert AppConfig defaults
    assert app_config.app_env == "development"
    assert app_config.debug is False

    # Assert CDCPipelineConfig defaults
    assert str(pipeline_config.api_base_url) == "https://wonder.cdc.gov/controller/datarequest/"
    assert pipeline_config.postgres_config.user == "postgres"
    assert pipeline_config.postgres_config.port == 5432


def test_setup_config_valid_custom_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_config with custom environment variables."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # PostgresConfig reads from these directly
    monkeypatch.setenv("PGUSER", "custom_user")
    monkeypatch.setenv("PGPORT", "5433")
    monkeypatch.setenv("CDC_WONDER_API_BASE_URL", "https://custom.api.cdc.gov/")

    # Provide PostgresConfig to PipelineConfig
    monkeypatch.setenv("CDC_WONDER_POSTGRES_CONFIG", '{"PGUSER": "custom_user", "PGPORT": 5433}')

    app_config, pipeline_config = setup_config()

    assert app_config.app_env == "production"
    assert app_config.log_level == "DEBUG"
    assert pipeline_config.postgres_config.user == "custom_user"
    assert pipeline_config.postgres_config.port == 5433
    assert str(pipeline_config.api_base_url) == "https://custom.api.cdc.gov/"


def test_setup_config_invalid_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_config raises ValidationError on invalid database port."""
    monkeypatch.setenv("CDC_WONDER_POSTGRES_CONFIG", '{"PGPORT": "invalid_port"}')
    with pytest.raises(ValidationError) as exc_info:
        setup_config()
    assert "Input should be a valid integer" in str(exc_info.value)


def test_setup_config_invalid_url(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_config raises ValidationError on invalid CDC WONDER URL."""
    monkeypatch.setenv("CDC_WONDER_API_BASE_URL", "not-a-valid-url")
    with pytest.raises(ValidationError) as exc_info:
        setup_config()
    assert "Input should be a valid URL" in str(exc_info.value)


def test_setup_config_invalid_boolean(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_config raises ValidationError on invalid boolean field."""
    monkeypatch.setenv("DEBUG", "not-a-boolean")
    with pytest.raises(ValidationError) as exc_info:
        setup_config()
    assert "Input should be a valid boolean" in str(exc_info.value)
