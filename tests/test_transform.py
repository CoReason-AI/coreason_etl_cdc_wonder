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
from unittest.mock import patch

import polars as pl
import pytest

from coreason_etl_cdc_wonder.config import NAMESPACE_CDC
from coreason_etl_cdc_wonder.transform import generate_coreason_id_batch, transform_bronze_to_silver


def test_generate_coreason_id_batch() -> None:
    """Test vectorized deterministic UUID generation."""
    input_data = pl.Series(["C34.9_1999", "I21.9_2000", None, ""])
    expected_uuids = [
        str(uuid.uuid5(NAMESPACE_CDC, "C34.9_1999")),
        str(uuid.uuid5(NAMESPACE_CDC, "I21.9_2000")),
        None,
        str(uuid.uuid5(NAMESPACE_CDC, "")),
    ]

    result = generate_coreason_id_batch(input_data)

    assert result.to_list() == expected_uuids


def test_transform_bronze_to_silver_missing_column() -> None:
    """Test missing raw_data column raises ValueError."""
    df = pl.DataFrame({"wrong_column": [1, 2, 3]})
    with pytest.raises(ValueError, match="DataFrame missing required 'raw_data' column"):
        transform_bronze_to_silver(df)


def test_transform_bronze_to_silver_success() -> None:
    """Test happy path transformation from raw bronze to typed silver."""
    raw_data = [
        {
            "c": [
                {"@v": "1999"},
                {"@v": "C34.9"},
                {"@v": "100"},
                {"@v": "100000"},
                {"@v": "100.0"},
            ]
        },
        {
            "c": [
                {"@v": "2000"},
                {"@v": "C50.9"},
                {"@v": "Suppressed"},
                {"@v": "50000"},
                {"@v": "Unreliable"},
            ]
        },
        {
            "c": [
                {"@v": "Totals"},
                {"@v": "500"},
            ]
        },
        {
            "c": [
                {"@v": ""},
                {"@v": ""},
            ]
        },
    ]

    df = pl.DataFrame({"raw_data": raw_data})

    result = transform_bronze_to_silver(df)

    assert result.shape == (2, 6)

    row_1999 = result.filter(pl.col("year") == 1999).to_dicts()[0]
    assert row_1999["icd_10_code"] == "C34.9"
    assert row_1999["deaths"] == 100.0
    assert row_1999["population"] == 100000.0
    assert row_1999["crude_rate"] == 100.0
    assert row_1999["coreason_id"] == str(uuid.uuid5(NAMESPACE_CDC, "C34.9_1999"))

    row_2000 = result.filter(pl.col("year") == 2000).to_dicts()[0]
    assert row_2000["icd_10_code"] == "C50.9"
    assert row_2000["deaths"] is None
    assert row_2000["population"] == 50000.0
    assert row_2000["crude_rate"] is None
    assert row_2000["coreason_id"] == str(uuid.uuid5(NAMESPACE_CDC, "C50.9_2000"))


def test_transform_bronze_to_silver_edge_cases() -> None:
    """Test handling of irregular raw_data structs."""

    raw_data_series = pl.Series(
        "raw_data",
        [
            {"c": {"@v": "1999"}},
            {"c": []},
            None,
            {"other_key": "val"},
            {"c": ["1999", "C34.9", "10", "1000", "1.0"]},
            {"c": [{"@v": "2001"}, {"@v": "C10"}, {"@v": "Not Applicable"}, {"@v": "bad_cast"}, {"@v": "1.0"}]},
        ],
        strict=False,
    )

    df = pl.DataFrame([raw_data_series])

    result = transform_bronze_to_silver(df)

    assert result.shape == (2, 6)
    row_1999 = result.filter(pl.col("year") == 1999).to_dicts()[0]
    assert row_1999["year"] == 1999
    assert row_1999["icd_10_code"] == "C34.9"
    assert row_1999["deaths"] == 10.0
    assert row_1999["population"] == 1000.0
    assert row_1999["crude_rate"] == 1.0

    row_2001 = result.filter(pl.col("year") == 2001).to_dicts()[0]
    assert row_2001["deaths"] is None
    assert row_2001["population"] is None


def test_transform_bronze_to_silver_exception() -> None:
    """Test that generic exceptions are caught and raised."""
    with patch("polars.DataFrame.with_columns", side_effect=Exception("mocked error")):
        df = pl.DataFrame({"raw_data": [{"c": []}]})
        with pytest.raises(Exception, match="mocked error"):
            transform_bronze_to_silver(df)


def test_extract_cells_inner() -> None:
    """Test the internal cell extraction function directly to hit edge cases."""
    from coreason_etl_cdc_wonder.transform import transform_bronze_to_silver

    # Passing edge cases to hit the extraction function early returns
    raw_data_series = pl.Series(
        "raw_data",
        [
            "not_a_dict",
            None,
            {"c": {"@v": "100"}},
            {"c": [100]},
        ],
        strict=False,
    )

    df = pl.DataFrame([raw_data_series])

    result = transform_bronze_to_silver(df)
    assert result.shape == (0, 6)


def test_extract_cells_inner_c_not_list() -> None:
    """Test when 'c' key is present but not a list or dict."""
    from coreason_etl_cdc_wonder.transform import transform_bronze_to_silver

    raw_data_series = pl.Series(
        "raw_data",
        [
            {"c": "some_string"},
            {"c": None},
            {"c": [{"@v": "2020"}, {"@v": "C10"}, {"@v": "bad"}, {"@v": "1000"}, {"@v": "1.0"}]},
        ],
        strict=False,
    )

    df = pl.DataFrame([raw_data_series])
    transform_bronze_to_silver(df)

    raw_data = [
        {
            "c": [
                {"@v": "1999"},
                {"@v": "C34.9"},
                {"@v": "abc_not_a_float"},  # Will trigger ValueError in float() -> None
                {"@v": "100000"},
                {"@v": "100.0"},
            ]
        }
    ]
    df2 = pl.DataFrame({"raw_data": raw_data})
    result2 = transform_bronze_to_silver(df2)
    assert result2.filter(pl.col("year") == 1999).to_dicts()[0]["deaths"] is None


def test_cast_numerical_value_error() -> None:
    """Test the cast_numerical function raises value error on parsing floats specifically"""
    from coreason_etl_cdc_wonder.transform import transform_bronze_to_silver

    raw_data = [
        {
            "c": [
                {"@v": "1999"},
                {"@v": "C34.9"},
                {"@v": "not_a_number"},
                {"@v": "100000"},
                {"@v": "100.0"},
            ]
        }
    ]

    df = pl.DataFrame({"raw_data": raw_data})

    result = transform_bronze_to_silver(df)
    assert result.to_dicts()[0]["deaths"] is None


def test_cast_numerical_value_error_manual_invocation() -> None:
    """Manually invoke _cast_numerical to hit line 99"""
    from coreason_etl_cdc_wonder.transform import transform_bronze_to_silver

    raw_data = [
        {
            "c": [
                {"@v": "1999"},
                {"@v": "C34.9"},
                {"@v": "i_am_not_a_float"},
                {"@v": "100000"},
                {"@v": "100.0"},
            ]
        }
    ]

    df = pl.DataFrame({"raw_data": raw_data})
    res = transform_bronze_to_silver(df)
    assert res.to_dicts()[0]["deaths"] is None


def test_cast_numerical_helper_direct() -> None:
    """Directly test the extracted cast_numerical helper to hit the ValueError path easily."""
    from coreason_etl_cdc_wonder.transform import _cast_numerical_helper

    assert _cast_numerical_helper("100.5") == 100.5
    assert _cast_numerical_helper(None) is None
    assert _cast_numerical_helper("") is None
    assert _cast_numerical_helper(" Suppressed ") is None
    assert _cast_numerical_helper("Unreliable") is None
    assert _cast_numerical_helper("this_is_not_a_float_or_suppressed_keyword") is None
