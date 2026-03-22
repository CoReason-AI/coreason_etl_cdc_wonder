-- Copyright (c) 2026 CoReason Inc.
--
-- This software is proprietary and dual-licensed.
-- Licensed under the Prosperity Public License 3.0 (the "License").
-- A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
-- For details, see the LICENSE file.
-- Commercial use beyond a 30-day trial requires a separate license.

{{ config(
    materialized='view',
    schema='gold',
    alias='icd10_to_seer_bridge'
) }}

-- AGENT INSTRUCTION: The BRD defines `gold_icd10_to_seer_bridge` as a mapping view aligning
-- CDC ICD-10 codes with `coreason_etl_seer` oncology codes. Since SEER is oncology-focused,
-- we map 'C' prefix ICD-10 codes (Neoplasms) primarily.
-- As the actual coreason_etl_seer data is out-of-scope for THIS pipeline's ingestion,
-- this model establishes the structural contract (bridge) that the Knowledge Graph expects.

WITH cdc_codes AS (
    SELECT DISTINCT
        icd_10_code,
        -- The primary domain key is generated here to match upstream SEER tables.
        -- SEER predominantly uses pure ICD-O-3 but maps to ICD-10 C-codes.
        SUBSTRING(icd_10_code FROM 1 FOR 3) AS icd_10_block
    FROM {{ ref('coreason_etl_cdc_wonder_silver_cdc_wonder_mortality') }}
    WHERE icd_10_code LIKE 'C%' OR icd_10_code LIKE 'D0%' OR icd_10_code LIKE 'D1%'
          OR icd_10_code LIKE 'D2%' OR icd_10_code LIKE 'D3%' OR icd_10_code LIKE 'D4%'
)

SELECT
    icd_10_code AS cdc_icd_10_code,
    icd_10_block AS mapped_seer_block_id,
    'ONCOLOGY' AS clinical_domain,
    -- Simple deterministic classification of whether a code is malignant (C) or in-situ/benign (D)
    CASE
        WHEN icd_10_code LIKE 'C%' THEN 'Malignant Neoplasm'
        ELSE 'In-Situ or Benign Neoplasm'
    END AS broad_seer_classification
FROM cdc_codes
