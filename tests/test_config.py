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

from coreason_etl_cdc_wonder.config import CDCPipelineConfig, CDCWonderRequestConfig


def test_cdcwonder_request_config_default() -> None:
    """Test the default configuration of CDCWonderRequestConfig."""
    config = CDCWonderRequestConfig()
    assert config.dataset_code == "D76"
    assert config.accept_datause_restrictions is True
    assert config.parameters == {}


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
    config = CDCWonderRequestConfig(dataset_code="D77", accept_datause_restrictions=False, parameters={"B_1": "D76.V1"})
    assert config.dataset_code == "D77"
    assert config.accept_datause_restrictions is False
    assert config.parameters == {"B_1": "D76.V1"}
