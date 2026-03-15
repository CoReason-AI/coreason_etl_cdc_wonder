# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

import uuid
from typing import Any

from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

NAMESPACE_CDC = uuid.uuid5(uuid.NAMESPACE_DNS, "cdc.gov")


class CDCWonderParametersConfig(BaseModel):
    """
    AGENT INSTRUCTION: This class defines the explicit parameters to be serialized
    into the CDC WONDER XML `<request-parameters>` payload.
    """

    group_by_1: str = Field(
        default="D76.V1",
        alias="B_1",
        description="The primary group-by parameter (e.g., D76.V1 for Age Group).",
    )
    group_by_2: str = Field(
        default="D76.V2",
        alias="B_2",
        description="The secondary group-by parameter (e.g., D76.V2 for ICD-10 113 Cause List).",
    )
    group_by_3: str = Field(
        default="D76.V9",
        alias="B_3",
        description="The tertiary group-by parameter (e.g., D76.V9 for State).",
    )
    measure_1: str = Field(
        default="D76.M1",
        alias="M_1",
        description="The primary measure (e.g., D76.M1 for Deaths).",
    )
    measure_2: str = Field(
        default="D76.M2",
        alias="M_2",
        description="The secondary measure (e.g., D76.M2 for Population).",
    )
    measure_3: str = Field(
        default="D76.M3",
        alias="M_3",
        description="The tertiary measure (e.g., D76.M3 for Crude Rate).",
    )
    custom_parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional custom parameters for the API.",
    )


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
    parameters: CDCWonderParametersConfig = Field(
        default_factory=CDCWonderParametersConfig,
        description="Explicitly defined query parameters for the WONDER API.",
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
