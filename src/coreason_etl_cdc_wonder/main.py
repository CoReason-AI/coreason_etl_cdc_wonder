# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder


from coreason_etl_cdc_wonder.config import AppConfig, CDCPipelineConfig
from coreason_etl_cdc_wonder.utils.logger import logger


def setup_config() -> tuple[AppConfig, CDCPipelineConfig]:
    """
    AGENT INSTRUCTION: Wires up the foundational configuration.
    Instantiates and validates AppConfig and CDCPipelineConfig.
    Raises ValidationError if required configuration parameters are malformed.
    """
    logger.info("Initializing configuration for coreason_etl_cdc_wonder")
    app_config = AppConfig()
    pipeline_config = CDCPipelineConfig()

    logger.info("Configuration validated successfully")
    return app_config, pipeline_config


def hello_world() -> str:
    logger.info("Hello World!")
    return "Hello World!"
