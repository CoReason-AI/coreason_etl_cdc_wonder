# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

from collections.abc import Iterable, Iterator
from typing import Any

import pytest
import requests

from coreason_etl_cdc_wonder.config import CDCPipelineConfig, CDCWonderParametersConfig, CDCWonderRequestConfig
from coreason_etl_cdc_wonder.resource import get_wonder_mortality_resource


def _mock_fetch_wonder_data(config: CDCPipelineConfig, delay_seconds: float = 2.0) -> Iterator[bytes]:
    """Mock for fetch_wonder_data."""
    _ = config
    _ = delay_seconds
    yield b"<r><c v='2020'/><c v='C34'/></r>"


def _mock_parse_wonder_xml_stream(stream: Iterable[bytes]) -> Iterator[dict[str, Any]]:
    """Mock for parse_wonder_xml_stream."""
    _ = stream
    yield {"raw_data": {"c": [{"@v": "2020"}, {"@v": "C34"}]}}


def test_get_wonder_mortality_resource(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that get_wonder_mortality_resource enriches rows correctly."""
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.fetch_wonder_data", _mock_fetch_wonder_data)
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.parse_wonder_xml_stream", _mock_parse_wonder_xml_stream)

    config = CDCPipelineConfig()

    # We call the function (which is a dlt.resource)
    resource = get_wonder_mortality_resource(config)

    # Iterate through the returned iterator
    rows = list(resource)

    assert len(rows) == 1
    row = rows[0]

    assert "ingestion_ts" in row
    assert isinstance(row["ingestion_ts"], str)

    assert "query_parameters" in row
    assert row["query_parameters"]["B_1"] == "D76.V1"

    assert "raw_data" in row
    assert row["raw_data"]["c"][0]["@v"] == "2020"
    assert row["raw_data"]["c"][1]["@v"] == "C34"


def _mock_parse_wonder_xml_stream_multiple(stream: Iterable[bytes]) -> Iterator[dict[str, Any]]:
    """Mock for parse_wonder_xml_stream returning multiple rows."""
    _ = stream
    yield {"raw_data": {"c": [{"@v": "2020"}, {"@v": "C34"}]}}
    yield {"raw_data": {"c": [{"@v": "2020"}, {"@v": "C35"}]}}


def test_get_wonder_mortality_resource_multiple_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test resource behavior with multiple rows returning from parser."""
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.fetch_wonder_data", _mock_fetch_wonder_data)
    monkeypatch.setattr(
        "coreason_etl_cdc_wonder.resource.parse_wonder_xml_stream", _mock_parse_wonder_xml_stream_multiple
    )

    config = CDCPipelineConfig()
    resource = get_wonder_mortality_resource(config)
    rows = list(resource)

    assert len(rows) == 2

    # Both should have the exact same ingestion_ts
    assert rows[0]["ingestion_ts"] == rows[1]["ingestion_ts"]

    # Both should have same query parameters
    assert rows[0]["query_parameters"] == rows[1]["query_parameters"]

    # Values should be different
    assert rows[0]["raw_data"]["c"][1]["@v"] == "C34"
    assert rows[1]["raw_data"]["c"][1]["@v"] == "C35"


def _mock_parse_wonder_xml_stream_empty(stream: Iterable[bytes]) -> Iterator[dict[str, Any]]:
    """Mock for parse_wonder_xml_stream returning empty stream."""
    _ = stream
    yield from []


def test_get_wonder_mortality_resource_empty_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test resource behavior when parsing yields no data."""
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.fetch_wonder_data", _mock_fetch_wonder_data)
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.parse_wonder_xml_stream", _mock_parse_wonder_xml_stream_empty)

    config = CDCPipelineConfig()
    resource = get_wonder_mortality_resource(config)
    rows = list(resource)

    assert len(rows) == 0


def _mock_fetch_wonder_data_exception(config: CDCPipelineConfig, delay_seconds: float = 2.0) -> Iterator[bytes]:
    """Mock for fetch_wonder_data throwing an exception."""
    _ = config
    _ = delay_seconds
    raise requests.exceptions.RequestException("CDC WONDER Timeout")


def test_get_wonder_mortality_resource_exception_bubbles_up(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test resource behavior when fetch request fails."""
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.fetch_wonder_data", _mock_fetch_wonder_data_exception)

    config = CDCPipelineConfig()
    resource = get_wonder_mortality_resource(config)

    from dlt.extract.exceptions import ResourceExtractionError

    with pytest.raises(ResourceExtractionError, match="CDC WONDER Timeout"):
        # The exception shouldn't happen until we actually list over the iterator
        # (generator evaluation). dlt bubbles it up as ResourceExtractionError.
        list(resource)


def test_get_wonder_mortality_resource_complex_parameters(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test resource enriches complex requested parameters cleanly."""
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.fetch_wonder_data", _mock_fetch_wonder_data)
    monkeypatch.setattr("coreason_etl_cdc_wonder.resource.parse_wonder_xml_stream", _mock_parse_wonder_xml_stream)

    custom_params = {"I_21": "D76.V21", "O_1": "1"}
    params_config = CDCWonderParametersConfig(
        B_1="D76.V2",
        custom_parameters=custom_params,
    )
    request_config = CDCWonderRequestConfig(parameters=params_config)
    config = CDCPipelineConfig(request_config=request_config)

    resource = get_wonder_mortality_resource(config)
    rows = list(resource)

    assert len(rows) == 1
    row = rows[0]

    # Assert parameters enriched cleanly in payload format
    assert row["query_parameters"]["B_1"] == "D76.V2"
    assert row["query_parameters"]["custom_parameters"] == custom_params
