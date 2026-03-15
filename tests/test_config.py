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

from coreason_etl_cdc_wonder.config import (
    NAMESPACE_CDC,
    CDCPipelineConfig,
    CDCWonderParametersConfig,
    CDCWonderRequestConfig,
)


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
