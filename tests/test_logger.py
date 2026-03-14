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

from coreason_etl_cdc_wonder.utils.logger import logger


def test_logger_exists() -> None:
    # Basic sanity check that logger is initialized
    assert logger is not None


@patch("pathlib.Path.exists", return_value=False)
@patch("pathlib.Path.mkdir")
def test_log_dir_creation(mock_mkdir: MagicMock, mock_exists: MagicMock) -> None:
    _ = mock_exists
    # We must reload the module to trigger the file-level log_path logic
    import importlib

    import coreason_etl_cdc_wonder.utils.logger

    importlib.reload(coreason_etl_cdc_wonder.utils.logger)
    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
