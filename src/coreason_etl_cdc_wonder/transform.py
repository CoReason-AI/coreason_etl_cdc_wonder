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

import polars as pl

from coreason_etl_cdc_wonder.config import NAMESPACE_CDC
from coreason_etl_cdc_wonder.utils.logger import logger


def generate_coreason_id_batch(s: pl.Series) -> pl.Series:
    """
    AGENT INSTRUCTION: Vectorized generation of deterministic UUIDv5 strings using Polars map_batches.
    Takes a Series of concatenated strings (e.g., icd10_code + year + group) and returns a Series
    of UUID strings. Any null inputs will return a null UUID.
    """

    def _to_uuid(val: str | None) -> str | None:
        if val is None:
            return None
        return str(uuid.uuid5(NAMESPACE_CDC, val))

    def _batch_apply(series: pl.Series) -> pl.Series:
        return pl.Series([_to_uuid(x) for x in series], dtype=pl.Utf8)

    return _batch_apply(s)


def _cast_numerical_helper(val: str | None) -> float | None:
    """Helper to cast numericals with value error catching. Extracted for easy testing."""
    if not val:
        return None
    val = val.strip().lower()
    if val in ("suppressed", "unreliable", "not applicable"):
        return None

    try:
        return float(val)
    except ValueError:
        return None


def transform_bronze_to_silver(df: pl.DataFrame) -> pl.DataFrame:
    """
    AGENT INSTRUCTION: Transforms raw Bronze JSONB data into a typed Silver Polars DataFrame.
    It extracts positional cells from the raw_data struct and generates the deterministic `coreason_id`.
    """
    logger.info("Transforming Bronze CDC WONDER data to Silver with vectorized identity resolution")

    if "raw_data" not in df.columns:
        msg = "DataFrame missing required 'raw_data' column"
        raise ValueError(msg)

    try:

        def _extract_cells(row: dict[str, Any] | None) -> list[str | None]:
            if not row or not isinstance(row, dict):
                return [None] * 5
            c_list = row.get("c", [])
            if not isinstance(c_list, list):
                if isinstance(c_list, dict):
                    c_list = [c_list]
                else:
                    return [None] * 5

            extracted: list[str | None] = []
            for cell in c_list:
                if isinstance(cell, dict):
                    extracted.append(str(cell.get("@v", "")))
                else:
                    extracted.append(str(cell))

            while len(extracted) < 5:
                extracted.append(None)
            return extracted

        df = df.with_columns(
            pl.col("raw_data").map_elements(_extract_cells, return_dtype=pl.List(pl.Utf8)).alias("_cells")
        )

        df = df.with_columns(
            [
                pl.col("_cells").list.get(0).alias("year"),
                pl.col("_cells").list.get(1).alias("icd_10_code"),
                pl.col("_cells").list.get(2).alias("deaths"),
                pl.col("_cells").list.get(3).alias("population"),
                pl.col("_cells").list.get(4).alias("crude_rate"),
            ]
        )

        df = df.filter(
            (pl.col("year").is_not_null())
            & (pl.col("icd_10_code").is_not_null())
            & (pl.col("year") != "")
            & (pl.col("icd_10_code") != "")
            & (pl.col("year").str.to_lowercase() != "totals")
        )

        df = df.with_columns(
            pl.concat_str([pl.col("icd_10_code"), pl.col("year")], separator="_")
            .map_batches(generate_coreason_id_batch)
            .alias("coreason_id")
        )

        df = df.with_columns(
            [
                pl.col("deaths").map_elements(_cast_numerical_helper, return_dtype=pl.Float64).alias("deaths"),
                pl.col("population").map_elements(_cast_numerical_helper, return_dtype=pl.Float64).alias("population"),
                pl.col("crude_rate").map_elements(_cast_numerical_helper, return_dtype=pl.Float64).alias("crude_rate"),
                pl.col("year").cast(pl.Int32, strict=False),
            ]
        )

        return df.select(["coreason_id", "year", "icd_10_code", "deaths", "population", "crude_rate"])

    except Exception:
        logger.exception("Failed to transform Bronze to Silver")
        raise
