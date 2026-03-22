-- Copyright (c) 2026 CoReason Inc.
--
-- This software is proprietary and dual-licensed.
-- Licensed under the Prosperity Public License 3.0 (the "License").
-- A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
-- For details, see the LICENSE file.
-- Commercial use beyond a 30-day trial requires a separate license.

{{ config(
    materialized='table',
    schema='gold',
    alias='disease_burden_index'
) }}

-- AGENT INSTRUCTION: The BRD defines `gold_disease_burden_index` as an analytics-ready table
-- mapping `icd_10_code` to historical mortality trends, leveraging the `coreason_id` for
-- deterministic entity matching in the Knowledge Graph.

WITH silver_metrics AS (
    SELECT
        coreason_id,
        icd_10_code,
        year,
        deaths,
        population,
        crude_rate
    FROM {{ ref('coreason_etl_cdc_wonder_silver_cdc_wonder_mortality') }}
),

disease_burden AS (
    SELECT
        coreason_id,
        icd_10_code,
        year,
        deaths,
        population,
        crude_rate,
        -- Add analytic flags
        CASE
            WHEN deaths IS NULL THEN TRUE
            ELSE FALSE
        END AS is_suppressed_or_unreliable,
        -- Historical burden tiering (placeholder for KG reasoning)
        CASE
            WHEN crude_rate > 100.0 THEN 'High Burden'
            WHEN crude_rate > 10.0 THEN 'Medium Burden'
            WHEN crude_rate > 0.0 THEN 'Low Burden'
            ELSE 'Unknown'
        END AS burden_tier
    FROM silver_metrics
)

SELECT * FROM disease_burden
