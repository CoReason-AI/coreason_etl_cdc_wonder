# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

import os
import uuid

import dlt
from hypothesis import given
from hypothesis import strategies as st
from hypothesis.provisional import urls

from coreason_etl_cdc_wonder.config import (
    NAMESPACE_CDC,
    AppConfig,
    CDCPipelineConfig,
    CDCWonderParametersConfig,
    CDCWonderRequestConfig,
    PostgresConfig,
)


def test_app_config_default() -> None:
    """Test the default configuration of AppConfig."""
    config = AppConfig()
    assert config.app_env == "development"
    assert config.debug is False
    assert config.secret_key == "replace-me-in-production"  # noqa: S105
    assert config.log_level == "INFO"


def test_app_config_custom_env() -> None:
    """Test AppConfig reading from environment variables."""
    os.environ["APP_ENV"] = "production"
    os.environ["DEBUG"] = "true"
    os.environ["SECRET_KEY"] = "supersecret"  # noqa: S105
    os.environ["LOG_LEVEL"] = "DEBUG"
    try:
        config = AppConfig()
        assert config.app_env == "production"
        assert config.debug is True
        assert config.secret_key == "supersecret"  # noqa: S105
        assert config.log_level == "DEBUG"
    finally:
        del os.environ["APP_ENV"]
        del os.environ["DEBUG"]
        del os.environ["SECRET_KEY"]
        del os.environ["LOG_LEVEL"]


@given(
    app_env=st.text(),
    debug=st.booleans(),
    secret_key=st.text(),
    log_level=st.text(),
)
def test_app_config_hypothesis(app_env: str, debug: bool, secret_key: str, log_level: str) -> None:
    """Property-based tests for AppConfig."""
    config = AppConfig(app_env=app_env, debug=debug, secret_key=secret_key, log_level=log_level)
    assert config.app_env == app_env
    assert config.debug is debug
    assert config.secret_key == secret_key
    assert config.log_level == log_level


def test_namespace_cdc() -> None:
    """Test the NAMESPACE_CDC constant is properly generated UUIDv5."""
    assert isinstance(NAMESPACE_CDC, uuid.UUID)
    expected_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, "cdc.gov")
    assert expected_uuid == NAMESPACE_CDC


def test_cdcwonder_parameters_config_default() -> None:
    """Test the default configuration of CDCWonderParametersConfig."""
    config = CDCWonderParametersConfig()
    assert config.group_by_1 == "D76.V1"
    assert config.group_by_2 == "D76.V2"
    assert config.group_by_3 == "D76.V9"
    assert config.measure_1 == "D76.M1"
    assert config.measure_2 == "D76.M2"
    assert config.measure_3 == "D76.M3"
    assert config.custom_parameters == {}


def test_cdcwonder_request_config_default() -> None:
    """Test the default configuration of CDCWonderRequestConfig."""
    config = CDCWonderRequestConfig()
    assert config.dataset_code == "D76"
    assert config.accept_datause_restrictions is True
    assert isinstance(config.parameters, CDCWonderParametersConfig)


def test_cdcpipeline_config_default() -> None:
    """Test the default configuration of CDCPipelineConfig."""
    config = CDCPipelineConfig()
    assert str(config.api_base_url) == "https://wonder.cdc.gov/controller/datarequest/"
    assert isinstance(config.request_config, CDCWonderRequestConfig)
    assert config.request_config.dataset_code == "D76"


def test_cdcpipeline_config_custom_env() -> None:
    """Test CDCPipelineConfig reading from environment variables."""
    os.environ["CDC_WONDER_API_BASE_URL"] = "https://custom.wonder.cdc.gov/controller/datarequest/"
    try:
        config = CDCPipelineConfig()
        assert str(config.api_base_url) == "https://custom.wonder.cdc.gov/controller/datarequest/"
    finally:
        del os.environ["CDC_WONDER_API_BASE_URL"]


def test_cdcwonder_request_config_custom() -> None:
    """Test custom configuration of CDCWonderRequestConfig."""
    custom_params = CDCWonderParametersConfig(B_1="D77.V1", custom_parameters={"F_1": "D77.V1"})
    config = CDCWonderRequestConfig(dataset_code="D77", accept_datause_restrictions=False, parameters=custom_params)
    assert config.dataset_code == "D77"
    assert config.accept_datause_restrictions is False
    assert isinstance(config.parameters, CDCWonderParametersConfig)
    assert config.parameters.group_by_1 == "D77.V1"
    assert config.parameters.custom_parameters == {"F_1": "D77.V1"}


def test_cdcwonder_parameters_config_alias() -> None:
    """Test CDCWonderParametersConfig alias."""
    config = CDCWonderParametersConfig(B_1="D76.V3", M_1="D76.M4")
    assert config.group_by_1 == "D76.V3"
    assert config.measure_1 == "D76.M4"


@given(
    b1=st.text(),
    b2=st.text(),
    b3=st.text(),
    m1=st.text(),
    m2=st.text(),
    m3=st.text(),
    custom=st.dictionaries(st.text(), st.text()),
)
def test_cdcwonder_parameters_config_hypothesis(
    b1: str, b2: str, b3: str, m1: str, m2: str, m3: str, custom: dict[str, str]
) -> None:
    """Property-based tests for CDCWonderParametersConfig."""
    config = CDCWonderParametersConfig(B_1=b1, B_2=b2, B_3=b3, M_1=m1, M_2=m2, M_3=m3, custom_parameters=custom)
    assert config.group_by_1 == b1
    assert config.group_by_2 == b2
    assert config.group_by_3 == b3
    assert config.measure_1 == m1
    assert config.measure_2 == m2
    assert config.measure_3 == m3
    assert config.custom_parameters == custom


@given(dataset_code=st.text(), accept_restrictions=st.booleans())
def test_cdcwonder_request_config_hypothesis(dataset_code: str, accept_restrictions: bool) -> None:
    """Property-based tests for CDCWonderRequestConfig."""
    config = CDCWonderRequestConfig(dataset_code=dataset_code, accept_datause_restrictions=accept_restrictions)
    assert config.dataset_code == dataset_code
    assert config.accept_datause_restrictions is accept_restrictions


@given(url=urls())
def test_cdcpipeline_config_hypothesis(url: str) -> None:
    """Property-based tests for CDCPipelineConfig with various valid URLs."""
    os.environ["CDC_WONDER_API_BASE_URL"] = url
    try:
        config = CDCPipelineConfig()
        # Pydantic HttpUrl normalizes the URL (e.g. lowercasing domain),
        # so we just check that it parses successfully instead of a strict string match.
        assert config.api_base_url is not None
    finally:
        del os.environ["CDC_WONDER_API_BASE_URL"]


def test_create_dlt_pipeline() -> None:
    """Test that the dlt pipeline is initialized with correct parameters and constraints."""
    config = CDCPipelineConfig()
    pipeline = config.create_dlt_pipeline()

    assert pipeline.pipeline_name == "coreason_etl_cdc_wonder"
    assert pipeline.dataset_name == "bronze"
    assert dlt.config.get("max_table_nesting") == 0


def test_postgres_config_default() -> None:
    """Test the default configuration of PostgresConfig."""
    config = PostgresConfig()
    assert config.host == "localhost"
    assert config.port == 5432
    assert config.user == "postgres"
    assert config.password == "postgres"  # noqa: S105
    assert config.database == "postgres"


@given(
    host=st.text(),
    port=st.integers(),
    user=st.text(),
    password=st.text(),
    database=st.text(),
)
def test_postgres_config_hypothesis(host: str, port: int, user: str, password: str, database: str) -> None:
    """Property-based tests for PostgresConfig."""
    config = PostgresConfig(PGHOST=host, PGPORT=port, PGUSER=user, PGPASSWORD=password, PGDATABASE=database)
    assert config.host == host
    assert config.port == port
    assert config.user == user
    assert config.password == password
    assert config.database == database
