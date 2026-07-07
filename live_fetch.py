import os
import polars as pl

# 1. Force the ultra-fast query payload (bypassing the .env file)
os.environ["CDC_WONDER_REQUEST_CONFIG"] = '{"dataset_code": "D76", "accept_datause_restrictions": true, "parameters": {"B_1": "D76.V1", "B_2": "D76.V2", "B_3": "*None*", "M_1": "D76.M1", "M_2": "D76.M2", "M_3": "D76.M3", "custom_parameters": {"B_4": "*None*", "B_5": "*None*", "O_V1_fmode": "freg", "O_V2_fmode": "freg", "O_aar": "aar_none", "O_aar_pop": "0000", "O_age": "D76.V5", "O_javascript": "on", "O_location": "D76.V9", "O_precision": "1", "O_rate_per": "100000", "O_show_suppressed": "false", "O_show_totals": "false", "O_show_zeros": "false", "O_timeout": "300", "O_title": "Test Query", "O_ucd": "D76.V2", "action-Send": "Send", "stage": "request", "V_D76.V1": "2020", "V_D76.V2": "*All*", "V_D76.V9": "01", "V_D76.V10": "*All*", "V_D76.V11": "*All*", "V_D76.V12": "*All*", "V_D76.V17": "*All*", "V_D76.V19": "*All*", "V_D76.V20": "*All*", "V_D76.V21": "*All*", "V_D76.V22": "*All*", "V_D76.V23": "*All*", "V_D76.V24": "*All*", "V_D76.V25": "*All*", "V_D76.V27": "*All*", "V_D76.V4": "*All*", "V_D76.V5": "*All*", "V_D76.V51": "*All*", "V_D76.V52": "*All*", "V_D76.V6": "00", "V_D76.V7": "*All*", "V_D76.V8": "*All*"}}}'

# 2. Prevent dlt from shredding the JSON array
os.environ["SCHEMA__MAX_TABLE_NESTING"] = "0"
os.environ["DATA_WRITER__MAX_TABLE_NESTING"] = "0"

# 3. Patch Polars to use the robust ADBC engine for Postgres JSONB
original_read = pl.read_database_uri
def patched_read(*args, **kwargs):
    kwargs["engine"] = "adbc"
    return original_read(*args, **kwargs)
pl.read_database_uri = patched_read

from coreason_etl_cdc_wonder.main import run_pipeline

if __name__ == "__main__":
    print("Initiating REAL network fetch to CDC WONDER...")
    run_pipeline()
