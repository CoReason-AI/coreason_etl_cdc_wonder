# Copyright (c) 2026 CoReason Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_etl_cdc_wonder

import importlib
import shutil
from pathlib import Path

from coreason_etl_cdc_wonder.utils.logger import logger


def test_logger_exports() -> None:
    """Test that logger is exported."""
    assert logger is not None


def test_logger_initialization_and_mkdir() -> None:
    """Test that the logger creates the directory if it does not exist."""
    import coreason_etl_cdc_wonder.utils.logger

    log_path = Path("logs")
    if log_path.exists():
        shutil.rmtree(log_path)

    importlib.reload(coreason_etl_cdc_wonder.utils.logger)
    assert log_path.exists()
    assert log_path.is_dir()
