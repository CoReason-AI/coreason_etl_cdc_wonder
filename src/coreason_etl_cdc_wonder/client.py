# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

import time
from typing import IO

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from coreason_etl_cdc_wonder.config import CDCPipelineConfig
from coreason_etl_cdc_wonder.payload import generate_wonder_xml_payload
from coreason_etl_cdc_wonder.utils.logger import logger


def _create_retry_session() -> requests.Session:
    """
    AGENT INSTRUCTION: Creates a requests Session with polite retry and backoff logic.
    This ensures the pipeline is robust against CDC WONDER throttling and timeouts.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return session


def fetch_wonder_data(config: CDCPipelineConfig, delay_seconds: float = 2.0) -> IO[bytes]:
    """
    AGENT INSTRUCTION: Fetches data from the CDC WONDER API via POST.
    It streams the response to enable memory-conscious parsing.

    Args:
        config: The pipeline configuration.
        delay_seconds: Polite delay before initiating the request.

    Returns:
        A file-like object yielding chunks of bytes from the HTTP response.
    """
    logger.info("Preparing to query CDC WONDER API", dataset=config.request_config.dataset_code)

    logger.debug("Applying polite delay before request", delay_seconds=delay_seconds)
    time.sleep(delay_seconds)

    payload = generate_wonder_xml_payload(config.request_config)

    endpoint = f"{str(config.api_base_url).rstrip('/')}/{config.request_config.dataset_code}"

    logger.info("Sending POST request to CDC WONDER API", endpoint=endpoint)

    session = _create_retry_session()

    response = session.post(
        url=endpoint,
        data={"request_xml": payload},
        stream=True,
        timeout=(10, 60),
    )

    response.raise_for_status()
    response.raw.decode_content = True

    logger.info("Successfully received streaming response from CDC WONDER API")
    return response.raw  # type: ignore[return-value]
