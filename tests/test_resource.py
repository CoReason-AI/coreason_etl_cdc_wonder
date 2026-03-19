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

from coreason_etl_cdc_wonder.config import CDCPipelineConfig
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


def test_get_wonder_mortality_resource(monkeypatch: Any) -> None:
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
