# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

from typing import Any

from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class CDCWonderRequestConfig(BaseModel):
    """
    AGENT INSTRUCTION: This class defines the configuration for the CDC WONDER API request.
    It MUST explicitly include the `accept_datause_restrictions` parameter.
    """

    dataset_code: str = Field(
        default="D76",
        description="The CDC WONDER dataset code to query (e.g., D76 for 1999-2020 Detailed Mortality).",
    )
    accept_datause_restrictions: bool = Field(
        default=True,
        description="Strictly required parameter to acknowledge WONDER data use restrictions. "
        "If False, the WONDER API returns HTML errors.",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional query parameters for the WONDER API.",
    )


class CDCPipelineConfig(BaseSettings):
    """
    AGENT INSTRUCTION: Global configuration for the coreason_etl_cdc_wonder pipeline.
    Environment variables map to these fields.
    """

    model_config = SettingsConfigDict(
        env_prefix="CDC_WONDER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_base_url: HttpUrl = Field(
        default=HttpUrl("https://wonder.cdc.gov/controller/datarequest/"),
        description="The base URL for the CDC WONDER API endpoint.",
    )
    request_config: CDCWonderRequestConfig = Field(
        default_factory=CDCWonderRequestConfig,
        description="Configuration for individual dataset requests.",
    )
