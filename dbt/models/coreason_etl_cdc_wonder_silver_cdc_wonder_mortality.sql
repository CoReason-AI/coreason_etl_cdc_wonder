-- Copyright (c) 2026 CoReason Inc.
--
-- This software is proprietary and dual-licensed.
-- Licensed under the Prosperity Public License 3.0 (the "License").
-- A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
-- For details, see the LICENSE file.
-- Commercial use beyond a 30-day trial requires a separate license.

{{ config(
    materialized='view',
    schema='silver',
    alias='coreason_etl_cdc_wonder_silver_cdc_wonder_mortality'
) }}

-- AGENT INSTRUCTION: This model reads from the Silver table that was materialized
-- upstream by the Python/Polars pipeline step. The Polars transform creates
-- `coreason_id` and extracts the logical columns. We just expose it cleanly here
-- so the Gold models can reference it seamlessly in the dbt DAG.

SELECT
    coreason_id,
    year,
    icd_10_code,
    deaths,
    population,
    crude_rate
FROM {{ source('silver', 'coreason_etl_cdc_wonder_silver_cdc_wonder_mortality') }}
