# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

from unittest.mock import MagicMock, patch

import pytest
import requests
from requests.exceptions import HTTPError

from coreason_etl_cdc_wonder.client import _create_retry_session, fetch_wonder_data
from coreason_etl_cdc_wonder.config import CDCPipelineConfig


def test_create_retry_session() -> None:
    """Test that the session is created with correct retry strategies."""
    session = _create_retry_session()
    assert isinstance(session, requests.Session)

    from requests.adapters import HTTPAdapter

    adapter = session.get_adapter("https://wonder.cdc.gov")
    assert isinstance(adapter, HTTPAdapter)
    assert adapter.max_retries.total == 5
    assert adapter.max_retries.backoff_factor == 2
    assert list(adapter.max_retries.status_forcelist) == [429, 500, 502, 503, 504]


@patch("coreason_etl_cdc_wonder.client.time.sleep")
@patch("coreason_etl_cdc_wonder.client._create_retry_session")
def test_fetch_wonder_data_success(mock_create_session: MagicMock, mock_sleep: MagicMock) -> None:
    """Test successful data fetching with streaming response."""
    config = CDCPipelineConfig()

    mock_session = MagicMock()
    mock_response = MagicMock()
    mock_response.iter_content.return_value = [b"<data>", b"</data>"]
    mock_session.post.return_value = mock_response
    mock_create_session.return_value = mock_session

    result = list(fetch_wonder_data(config, delay_seconds=1.5))

    mock_sleep.assert_called_once_with(1.5)
    mock_session.post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    assert result == [b"<data>", b"</data>"]

    # Verify endpoint construction
    _call_args, call_kwargs = mock_session.post.call_args
    assert call_kwargs["url"] == "https://wonder.cdc.gov/controller/datarequest/D76"


@patch("coreason_etl_cdc_wonder.client.time.sleep")
@patch("coreason_etl_cdc_wonder.client._create_retry_session")
def test_fetch_wonder_data_http_error(mock_create_session: MagicMock, mock_sleep: MagicMock) -> None:
    """Test that an HTTP error is properly raised."""
    config = CDCPipelineConfig()

    mock_session = MagicMock()
    mock_response = MagicMock()

    # Simulate an HTTP error when calling raise_for_status
    mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
    mock_session.post.return_value = mock_response
    mock_create_session.return_value = mock_session

    with pytest.raises(HTTPError):
        list(fetch_wonder_data(config, delay_seconds=0.0))

    mock_sleep.assert_called_once_with(0.0)
    mock_session.post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
