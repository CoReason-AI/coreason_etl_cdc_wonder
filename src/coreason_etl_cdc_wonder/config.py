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

import dlt
from dlt.pipeline.pipeline import Pipeline
from pydantic import BaseModel, Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

NAMESPACE_CDC = uuid.uuid5(uuid.NAMESPACE_DNS, "cdc.gov")


class AppConfig(BaseSettings):
    """
    AGENT INSTRUCTION: Base application configuration matching 12-Factor principles.
    Reads global environment variables like APP_ENV, DEBUG, LOG_LEVEL, etc.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(
        default="development",
        description="The environment the application is running in (e.g. development, testing, production).",
    )
    debug: bool = Field(
        default=False,
        description="Whether debugging is enabled.",
    )
    secret_key: str = Field(
        default="replace-me-in-production",
        description="Secret key for cryptographic signing.",
    )
    log_level: str = Field(
        default="INFO",
        description="The logging level (e.g. DEBUG, INFO, WARNING, ERROR).",
    )


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


class PostgresConfig(BaseModel):
    """
    AGENT INSTRUCTION: PostgreSQL connection credentials.
    Variables map to standard Postgres environment variables: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE.
    """

    host: str = Field(
        default="localhost",
        description="The host for the Postgres database.",
        alias="PGHOST",
    )
    port: int = Field(
        default=5432,
        description="The port for the Postgres database.",
        alias="PGPORT",
    )
    user: str = Field(
        default="postgres",
        description="The username for the Postgres database.",
        alias="PGUSER",
    )
    password: str = Field(
        default="postgres",
        description="The password for the Postgres database.",
        alias="PGPASSWORD",
    )
    database: str = Field(
        default="postgres",
        description="The database name for the Postgres database.",
        alias="PGDATABASE",
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
    postgres_config: PostgresConfig = Field(
        default_factory=PostgresConfig,
        description="Configuration for the PostgreSQL database connection.",
    )

    def create_dlt_pipeline(self) -> Pipeline:
        """
        AGENT INSTRUCTION: Creates and configures the dlt pipeline.
        It strictly sets `max_table_nesting=0` to prevent schema shredding
        of the generic CDC WONDER XML arrays in the Bronze layer.
        """
        pipeline = dlt.pipeline(
            pipeline_name="coreason_etl_cdc_wonder",
            destination="postgres",
            dataset_name="bronze",
            progress="log",
            export_schema_path="schemas/export",
        )
        dlt.config["max_table_nesting"] = 0
        return pipeline
