# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

import sys
from unittest.mock import patch

from coreason_etl_cdc_wonder.utils.logger import logger


def test_logger_exports() -> None:
    """Test that logger is exported."""
    assert logger is not None


def test_logger_initialization_and_mkdir() -> None:
    """Test that the logger creates the directory if it does not exist."""

    # By mocking pathlib.Path directly during the reload, we can intercept the call.
    # We must mock it before import to ensure it works correctly on the next reload.

    with patch("pathlib.Path") as mock_path_cls:
        mock_path_instance = mock_path_cls.return_value
        mock_path_instance.exists.return_value = False

        # Prevent the logger from creating an actual file or printing to stderr during test
        with patch("loguru.logger.add"), patch("loguru.logger.remove"):
            if "coreason_etl_cdc_wonder.utils.logger" in sys.modules:
                del sys.modules["coreason_etl_cdc_wonder.utils.logger"]

            import coreason_etl_cdc_wonder.utils.logger

        mock_path_cls.assert_any_call("logs")
        mock_path_instance.exists.assert_called()
        mock_path_instance.mkdir.assert_called_with(parents=True, exist_ok=True)

    # Restore normal state for other tests
    if "coreason_etl_cdc_wonder.utils.logger" in sys.modules:
        del sys.modules["coreason_etl_cdc_wonder.utils.logger"]
    import coreason_etl_cdc_wonder.utils.logger  # noqa: F401
