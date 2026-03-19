# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import dlt

from coreason_etl_cdc_wonder.client import fetch_wonder_data
from coreason_etl_cdc_wonder.config import CDCPipelineConfig
from coreason_etl_cdc_wonder.parser import parse_wonder_xml_stream
from coreason_etl_cdc_wonder.utils.logger import logger


@dlt.resource(name="cdc_wonder_mortality_raw", write_disposition="append")  # type: ignore[misc]
def get_wonder_mortality_resource(config: CDCPipelineConfig) -> Iterator[dict[str, Any]]:
    """
    AGENT INSTRUCTION: A dlt resource that streams mortality data from the CDC WONDER API.
    It reads chunks, parses them iteratively for memory safety, and enriches each row
    with ingestion metadata (ingestion_ts and query_parameters) as required by the Bronze schema.
    """
    logger.info("Initializing CDC WONDER mortality resource", dataset=config.dataset_code)

    stream = fetch_wonder_data(config=config)
    parsed_rows = parse_wonder_xml_stream(stream=stream)

    ingestion_ts = datetime.now(UTC).isoformat()

    # Store query parameters for provenance
    query_params_dict = config.request_config.parameters.model_dump(by_alias=True)

    for row in parsed_rows:
        yield {
            "query_parameters": query_params_dict,
            "ingestion_ts": ingestion_ts,
            "raw_data": row["raw_data"],
        }
