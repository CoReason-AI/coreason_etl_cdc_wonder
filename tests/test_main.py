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
from pydantic_settings.exceptions import SettingsError

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


def test_setup_config_complex_nested_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_config parses complex nested JSON configuration correctly."""
    json_config = """
    {
        "dataset_code": "D77",
        "accept_datause_restrictions": false,
        "parameters": {
            "B_1": "Custom.V1",
            "M_1": "Custom.M1",
            "custom_parameters": {
                "Extra": "Value"
            }
        }
    }
    """
    monkeypatch.setenv("CDC_WONDER_REQUEST_CONFIG", json_config)

    _app_config, pipeline_config = setup_config()

    # Verify parsing
    assert pipeline_config.request_config.dataset_code == "D77"
    assert pipeline_config.request_config.accept_datause_restrictions is False
    assert pipeline_config.request_config.parameters.group_by_1 == "Custom.V1"
    assert pipeline_config.request_config.parameters.measure_1 == "Custom.M1"
    assert pipeline_config.request_config.parameters.custom_parameters == {"Extra": "Value"}


def test_setup_config_malformed_json(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_config raises SettingsError on malformed JSON payload."""
    # JSON missing closing brace
    monkeypatch.setenv("CDC_WONDER_REQUEST_CONFIG", '{"dataset_code": "D77"')

    with pytest.raises(SettingsError) as exc_info:
        setup_config()

    assert "error parsing value" in str(exc_info.value)


def test_setup_config_empty_string_for_integer(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test setup_config raises ValidationError for empty string mapped to integer."""
    monkeypatch.setenv("CDC_WONDER_POSTGRES_CONFIG", '{"PGPORT": ""}')
    with pytest.raises(ValidationError) as exc_info:
        setup_config()
    assert "Input should be a valid integer" in str(exc_info.value)


def test_run_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the complete pipeline orchestration wrapper."""
    from unittest.mock import MagicMock

    import coreason_etl_cdc_wonder.resource
    from coreason_etl_cdc_wonder.main import run_pipeline

    mock_pipeline = MagicMock()
    mock_pipeline.run = MagicMock()

    # Mock the setup to prevent real dlt init
    monkeypatch.setattr(
        "coreason_etl_cdc_wonder.main.setup_config",
        MagicMock(return_value=(MagicMock(), MagicMock(create_dlt_pipeline=MagicMock(return_value=mock_pipeline)))),
    )

    # Mock the resource using its actual module, not main
    monkeypatch.setattr(coreason_etl_cdc_wonder.resource, "get_wonder_mortality_resource", MagicMock())

    # Mock Polars to return an empty DF so we can test the exception path quickly
    monkeypatch.setattr("polars.read_database_uri", MagicMock(side_effect=Exception("Database down")))

    run_pipeline()
    mock_pipeline.run.assert_called_once()


def test_run_pipeline_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the complete pipeline orchestration wrapper success path."""
    from unittest.mock import MagicMock

    import polars as pl

    import coreason_etl_cdc_wonder.resource
    from coreason_etl_cdc_wonder.main import run_pipeline

    mock_pipeline = MagicMock()
    mock_pipeline.run = MagicMock()
    mock_pipeline_config = MagicMock()
    mock_pipeline_config.create_dlt_pipeline.return_value = mock_pipeline
    mock_pipeline_config.postgres_config.user = "user"
    mock_pipeline_config.postgres_config.password = "pass"  # noqa: S105
    mock_pipeline_config.postgres_config.host = "host"
    mock_pipeline_config.postgres_config.port = 5432
    mock_pipeline_config.postgres_config.database = "db"

    monkeypatch.setattr(
        "coreason_etl_cdc_wonder.main.setup_config", MagicMock(return_value=(MagicMock(), mock_pipeline_config))
    )

    monkeypatch.setattr(coreason_etl_cdc_wonder.resource, "get_wonder_mortality_resource", MagicMock())

    # Mock successful DB read and return some fake raw data
    raw_data = [{"c": [{"@v": "1999"}, {"@v": "C34.9"}, {"@v": "100"}, {"@v": "100000"}, {"@v": "100.0"}]}]
    mock_df = pl.DataFrame({"raw_data": raw_data})
    monkeypatch.setattr("polars.read_database_uri", MagicMock(return_value=mock_df))

    # Mock write
    mock_write = MagicMock()
    monkeypatch.setattr("polars.DataFrame.write_database", mock_write)

    run_pipeline()

    mock_pipeline.run.assert_called_once()
    mock_write.assert_called_once()
